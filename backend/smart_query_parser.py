"""
智能查询解析模块 (Smart Query Parser)

该模块实现智能文本解析功能，将用户输入的自然语言查询文本解析为结构化的搜索参数。
利用 LLM（大语言模型）分析用户查询意图，提取关键词和筛选条件。
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from customer_category_loader import CustomerCategoryLookup
from pathlib import Path

# 中软国际实体名单
CHINASOFT_ENTITY_NAMES: List[str] = [
    "中软国际科技服务有限公司",
    "上海中软华腾软件系统有限公司",
    "北京中软国际信息技术有限公司",
    "深圳中软国际科技服务有限公司",
    "北京中软国际科技服务有限公司",
    "中软国际（上海）科技服务有限公司",
    "中软国际科技服务（湖南）有限公司",
    "Chinasoft International Technology Service (Hong Kong) Limited",
]

DEFAULT_CUSTOMER_CATEGORY_PATH = (
    Path(__file__).resolve().parents[1] / "金融客户白名单.xlsx"
)


class SmartQueryParser:
    """
    智能查询解析器
    
    将用户的自然语言查询解析为结构化的搜索参数，包括：
    - keywords: 搜索关键词
    - filters: 筛选条件（金额、日期、分类等）
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化智能查询解析器
        
        Args:
            api_key: DeepSeek API 密钥，如果不提供则尝试从环境变量读取
        """
        self.api_key = api_key or os.getenv("CONTRACT_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("警告: 未检测到 DeepSeek API 密钥（请设置 CONTRACT_API_KEY），智能解析功能将无法使用。")
        
        self.api_url = "http://model.aicc.chinasoftinc.com/v1/chat/completions"
        self.model = "DeepSeekV3"
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        
        # 加载客户分类层级
        self._load_customer_categories()
    
    def _load_customer_categories(self) -> None:
        """加载客户分类层级供 Prompt 使用"""
        mapping_path_env = os.getenv("CUSTOMER_CATEGORY_MAPPING_PATH")
        if mapping_path_env:
            mapping_path = Path(mapping_path_env).expanduser()
        elif DEFAULT_CUSTOMER_CATEGORY_PATH.exists():
            mapping_path = DEFAULT_CUSTOMER_CATEGORY_PATH
        else:
            mapping_path = None
        
        if mapping_path:
            self.category_lookup = CustomerCategoryLookup(str(mapping_path))
            self.category_hierarchy = self.category_lookup.get_category_hierarchy()
        else:
            self.category_lookup = None
            self.category_hierarchy = {}
    
    def _get_current_year(self) -> int:
        """获取当前年份"""
        return datetime.now().year
    
    def _build_prompt(self, query_text: str) -> str:
        """
        构建 LLM 解析 Prompt
        
        Args:
            query_text: 用户输入的自然语言查询文本
            
        Returns:
            格式化的 Prompt 字符串
        """
        current_year = self._get_current_year()
        last_year = current_year - 1
        
        # 构建实体名单
        entity_list = "\n".join(f"  - \"{name}\"" for name in CHINASOFT_ENTITY_NAMES)
        
        # 构建客户分类枚举
        category_list = []
        full_category_mode = True
        
        # 预先计算分类部分长度，防止 Context Explode (上下文溢出)
        temp_category_list = []
        for level1, level2_list in self.category_hierarchy.items():
            if level2_list:
                level2_str = ", ".join(f'"{l2}"' for l2 in level2_list)
                temp_category_list.append(f'  - 一级分类: "{level1}", 二级分类: [{level2_str}]')
            else:
                temp_category_list.append(f'  - 一级分类: "{level1}", 二级分类: []')
        
        category_full_str = "\n".join(temp_category_list)
        
        # 如果分类字符串超过 5000 字符，降级为只提供一级分类
        if len(category_full_str) > 5000:
            print(f"警告: 客户分类列表过长 ({len(category_full_str)}字符)，已启用简化模式")
            full_category_mode = False
            category_list = [f'  - 一级分类: "{l1}" (请根据语义推断二级分类)' for l1 in self.category_hierarchy.keys()]
            category_text = "\n".join(category_list)
        else:
            category_text = category_full_str if temp_category_list else "  （暂无预定义分类）"
        
        prompt = f"""你是一个专业的合同搜索助手。用户会输入一段自然语言描述，描述他们想要搜索的合同条件。

请仔细分析用户输入，将其解析为结构化的搜索参数。

**当前时间信息**:
- 当前年份: {current_year}
- "去年" 指: {last_year}年
- "今年" 指: {current_year}年

**系统支持的筛选条件及其枚举值**:

1. 我方实体 (our_entity): 只能从以下列表中选择
{entity_list}

2. 客户分类 (customer_category): 按照以下层级结构
{category_text}

3. 金额范围 (amount): 支持最小值和最大值
   - 用户可能说 "大于500万" (amount_min: 5000000)
   - 用户可能说 "小于100万" (amount_max: 1000000)
   - 用户可能说 "500万到1000万" (amount_min: 5000000, amount_max: 10000000)
   - 注意：请将"万"转换为实际数字（1万=10000）

4. 签订日期范围 (date): 支持起始日期和结束日期
   - "去年的合同": date_start: "{last_year}-01-01", date_end: "{last_year}-12-31"
   - "今年的合同": date_start: "{current_year}-01-01", date_end: "{current_year}-12-31"
   - "2023年": date_start: "2023-01-01", date_end: "2023-12-31"
   - 日期格式统一为 YYYY-MM-DD

5. 关键词 (keywords): 用于全文检索的关键词列表
   - 如 "光缆采购"、"服务器维修" 等描述性词语

**解析规则**:
1. 严格按照上述枚举值进行匹配，不要臆造不存在的分类或状态
2. 如果用户提到的分类不在列表中，尝试找最接近的匹配项，或将其作为关键词处理
3. 金额单位请统一转换为人民币元（万=10000）
4. 如果无法确定某个筛选条件，请将该字段设为 null
5. 关键词应提取用户描述中与合同内容相关的核心词汇

**Few-Shot 示例**:

示例1:
用户输入: "请查找去年签订的金额大于500万且客户是电信部门的关于光缆采购的合同"
输出:
{{
  "keywords": ["光缆采购"],
  "filters": {{
    "date_start": "{last_year}-01-01",
    "date_end": "{last_year}-12-31",
    "amount_min": 5000000,
    "amount_max": null,
    "our_entity": null,
    "customer_category_level1": "电信",
    "customer_category_level2": null
  }}
}}

示例2:
用户输入: "查找所有关于服务器维修的记录"
输出:
{{
  "keywords": ["服务器维修"],
  "filters": {{
    "date_start": null,
    "date_end": null,
    "amount_min": null,
    "amount_max": null,
    "our_entity": null,
    "customer_category_level1": null,
    "customer_category_level2": null
  }}
}}

示例3:
用户输入: "只要看金额大于一千万的大单"
输出:
{{
  "keywords": [],
  "filters": {{
    "date_start": null,
    "date_end": null,
    "amount_min": 10000000,
    "amount_max": null,
    "our_entity": null,
    "customer_category_level1": null,
    "customer_category_level2": null
  }}
}}

示例4:
用户输入: "找中软国际科技服务有限公司和银行客户签的合同"
输出:
{{
  "keywords": [],
  "filters": {{
    "date_start": null,
    "date_end": null,
    "amount_min": null,
    "amount_max": null,
    "our_entity": "中软国际科技服务有限公司",
    "customer_category_level1": "金融",
    "customer_category_level2": "银行"
  }}
}}

---

现在，请解析以下用户输入:

用户输入: "{query_text}"

请返回 JSON 格式的结果，格式如下:
{{
  "keywords": ["关键词1", "关键词2"],
  "filters": {{
    "date_start": "YYYY-MM-DD或null",
    "date_end": "YYYY-MM-DD或null",
    "amount_min": 数字或null,
    "amount_max": 数字或null,
    "our_entity": "实体名称或null",
    "customer_category_level1": "一级分类或null",
    "customer_category_level2": "二级分类或null"
  }}
}}

请确保输出为有效的 JSON 格式。
"""
        return prompt
    
    def _call_llm_api(self, prompt: str) -> str:
        """
        调用 LLM API
        
        Args:
            prompt: 发送给 API 的提示词
            
        Returns:
            API 返回的文本内容
            
        Raises:
            RuntimeError: API 密钥未配置时抛出
            Exception: API 调用失败时抛出
        """
        if not self.api_key:
            raise RuntimeError("DeepSeek API 密钥未配置（请设置环境变量 CONTRACT_API_KEY）")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的合同搜索助手，擅长将自然语言查询解析为结构化搜索参数。请严格按照要求的 JSON 格式返回结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000,
            "top_p": 0.95,
            "stream": False
        }
        
        import time
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url, 
                    headers=headers, 
                    json=data, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    choices = result.get("choices")
                    if choices and isinstance(choices, list):
                        message = choices[0].get("message", {})
                        content = message.get("content")
                        if content:
                            return content.strip()
                    raise Exception(f"API 响应格式错误: {result}")
                
                elif response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        print(f"API 调用频率限制，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception("API 调用频率限制，重试次数已用完")
                else:
                    error_msg = f"API 调用失败，状态码: {response.status_code}, 响应: {response.text}"
                    if attempt < self.max_retries - 1:
                        print(f"API 错误，重试中... 错误信息: {error_msg}")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise Exception(error_msg)
                        
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    print(f"网络错误，重试中... 错误信息: {str(e)}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise Exception(f"网络请求失败: {str(e)}")
        
        raise Exception("API 调用失败，已达到最大重试次数")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析 API 返回的 JSON 响应
        
        Args:
            response_text: API 返回的文本
            
        Returns:
            解析后的字典对象
            
        Raises:
            Exception: JSON 解析失败时抛出
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            try:
                cleaned_text = response_text.strip()
                
                # 查找 JSON 开始和结束位置
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = cleaned_text[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    raise Exception("响应中未找到有效的 JSON 格式")
                    
            except json.JSONDecodeError:
                # 尝试移除 markdown 代码块标记
                if '```json' in response_text:
                    start_marker = response_text.find('```json') + 7
                    end_marker = response_text.find('```', start_marker)
                    if end_marker != -1:
                        json_str = response_text[start_marker:end_marker].strip()
                        return json.loads(json_str)
                
                elif '```' in response_text:
                    start_marker = response_text.find('```') + 3
                    end_marker = response_text.find('```', start_marker)
                    if end_marker != -1:
                        json_str = response_text[start_marker:end_marker].strip()
                        return json.loads(json_str)
                
                raise Exception(f"JSON 解析失败，原始响应: {response_text[:500]}")
    
    def _validate_and_clean_result(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和清理解析结果
        
        Args:
            parsed: 原始解析结果
            
        Returns:
            清理后的结果
        """
        result = {
            "keywords": [],
            "filters": {
                "date_start": None,
                "date_end": None,
                "amount_min": None,
                "amount_max": None,
                "our_entity": None,
                "customer_category_level1": None,
                "customer_category_level2": None
            }
        }
        
        # 提取关键词
        keywords = parsed.get("keywords", [])
        if isinstance(keywords, list):
            result["keywords"] = [str(k).strip() for k in keywords if k and str(k).strip()]
        elif isinstance(keywords, str) and keywords.strip():
            result["keywords"] = [keywords.strip()]
        
        # 提取筛选条件
        filters = parsed.get("filters", {})
        if isinstance(filters, dict):
            # 日期
            if filters.get("date_start"):
                date_start = str(filters["date_start"]).strip()
                if date_start.lower() != "null" and re.match(r'^\d{4}-\d{2}-\d{2}$', date_start):
                    result["filters"]["date_start"] = date_start
            
            if filters.get("date_end"):
                date_end = str(filters["date_end"]).strip()
                if date_end.lower() != "null" and re.match(r'^\d{4}-\d{2}-\d{2}$', date_end):
                    result["filters"]["date_end"] = date_end
            
            # 金额
            if filters.get("amount_min") is not None:
                try:
                    amount_min = filters["amount_min"]
                    if isinstance(amount_min, (int, float)):
                        result["filters"]["amount_min"] = float(amount_min)
                    elif isinstance(amount_min, str) and amount_min.lower() != "null":
                        result["filters"]["amount_min"] = float(amount_min.replace(",", ""))
                except (ValueError, TypeError):
                    pass
            
            if filters.get("amount_max") is not None:
                try:
                    amount_max = filters["amount_max"]
                    if isinstance(amount_max, (int, float)):
                        result["filters"]["amount_max"] = float(amount_max)
                    elif isinstance(amount_max, str) and amount_max.lower() != "null":
                        result["filters"]["amount_max"] = float(amount_max.replace(",", ""))
                except (ValueError, TypeError):
                    pass
            
            # 我方实体
            our_entity = filters.get("our_entity")
            if our_entity and str(our_entity).lower() != "null":
                entity_str = str(our_entity).strip()
                # 验证实体是否在允许列表中
                if entity_str in CHINASOFT_ENTITY_NAMES:
                    result["filters"]["our_entity"] = entity_str
                else:
                    # 尝试模糊匹配
                    for entity in CHINASOFT_ENTITY_NAMES:
                        if entity_str in entity or entity in entity_str:
                            result["filters"]["our_entity"] = entity
                            break
            
            # 客户分类
            level1 = filters.get("customer_category_level1")
            if level1 and str(level1).lower() != "null":
                level1_str = str(level1).strip()
                # 验证是否在允许的一级分类中
                if level1_str in self.category_hierarchy:
                    result["filters"]["customer_category_level1"] = level1_str
                else:
                    # 尝试模糊匹配
                    for cat in self.category_hierarchy.keys():
                        if level1_str in cat or cat in level1_str:
                            result["filters"]["customer_category_level1"] = cat
                            break
            
            level2 = filters.get("customer_category_level2")
            if level2 and str(level2).lower() != "null":
                level2_str = str(level2).strip()
                # 如果有一级分类，验证二级分类是否匹配
                parent_level1 = result["filters"]["customer_category_level1"]
                if parent_level1 and parent_level1 in self.category_hierarchy:
                    allowed_level2 = self.category_hierarchy[parent_level1]
                    if level2_str in allowed_level2:
                        result["filters"]["customer_category_level2"] = level2_str
                    else:
                        # 尝试模糊匹配
                        for l2 in allowed_level2:
                            if level2_str in l2 or l2 in level2_str:
                                result["filters"]["customer_category_level2"] = l2
                                break
        
        return result
    
    def parse(self, query_text: str) -> Dict[str, Any]:
        """
        解析用户的自然语言查询
        
        Args:
            query_text: 用户输入的自然语言查询文本
            
        Returns:
            结构化的搜索参数，包含 keywords 和 filters
        """
        if not query_text or not query_text.strip():
            return {
                "success": False,
                "error": "查询文本不能为空",
                "keywords": [],
                "filters": {}
            }
        
        if not self.api_key:
            return {
                "success": False,
                "error": "API 密钥未配置，请设置环境变量 CONTRACT_API_KEY",
                "keywords": [],
                "filters": {}
            }
        
        try:
            # 构建 Prompt
            prompt = self._build_prompt(query_text.strip())
            
            # 调用 LLM API
            response_text = self._call_llm_api(prompt)
            print(f"LLM 原始响应: {response_text[:500]}...")
            
            # 解析 JSON 响应
            parsed = self._parse_json_response(response_text)
            
            # 验证和清理结果
            result = self._validate_and_clean_result(parsed)
            
            return {
                "success": True,
                "keywords": result["keywords"],
                "filters": result["filters"],
                "raw_response": response_text
            }
            
        except Exception as e:
            print(f"智能解析失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "keywords": [],
                "filters": {}
            }


# 单例实例
_parser_instance: Optional[SmartQueryParser] = None


def get_smart_query_parser() -> SmartQueryParser:
    """获取智能查询解析器单例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SmartQueryParser()
    return _parser_instance


# 使用示例
if __name__ == "__main__":
    parser = SmartQueryParser()
    
    # 测试用例
    test_queries = [
        "请查找去年签订的金额大于500万且客户是电信部门的关于光缆采购的合同",
        "查找所有关于服务器维修的记录",
        "只要看金额大于一千万的大单",
        "找中软国际科技服务有限公司和银行客户签的合同"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        result = parser.parse(query)
        print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
