import requests
import json
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import os
from sentence_transformers import SentenceTransformer
import numpy as np

class MetadataExtractor:
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化元数据提取器
        
        Args:
            api_key: Qwen API密钥，如果不提供则使用默认密钥
        """
        self.api_key = api_key or "sk-c1aeeb5e64a34898b793f6040bda3473"
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = "qwen-plus-2025-07-28"
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        
        # 初始化向量模型（与正文内容使用相同的模型）
        try:
            self.vector_model = SentenceTransformer('BAAI/bge-base-zh')
            print("向量模型加载成功")
        except Exception as e:
            print(f"向量模型加载失败: {e}")
            self.vector_model = None
    
    def _get_prompt_template(self, contract_type: str = "unknown") -> str:
        """
        根据合同类型获取相应的Prompt模板
        
        Args:
            contract_type: 合同方向，"金融方向"、"互联网方向"、"电信方向"或"其他"
        
        Returns:
            格式化的Prompt字符串
        """
        
        # 精简的提取字段（只保留用户要求的7个字段）
        fields_to_extract = """
        必须提取的字段：
        - party_a: 甲方名称
        - party_b: 乙方名称
        - contract_type: 合同方向（金融方向【银行、保险、证券】、互联网方向、电信方向、其他）
        - contract_amount: 合同金额（数字，如果有多个金额取总金额）
        - project_description: 合同内容（项目描述或服务内容）
        - positions: 岗位信息
        - personnel_list: 相关人员清单
        """
        
        base_template = """
你是一个专业的合同分析助手。请仔细分析以下合同文本，并提取关键信息。

必须提取的字段：
- party_a: 甲方名称
- party_b: 乙方名称
- contract_type: 合同方向（金融方向【银行、保险、证券】、互联网方向、电信方向、其他）
- contract_amount: 合同金额（数字，如果有多个金额取总金额）
- project_description: 合同内容（项目描述或服务内容）
- positions: 岗位信息
- personnel_list: 相关人员清单

请按照以下要求进行提取：
1. 仔细阅读合同全文
2. 准确识别各个字段的信息
3. 如果某个字段在合同中没有明确提及，请设置为null
4. 金额请提取数字部分，不包含货币符号
5. 返回结果必须是有效的JSON格式
6. 只提取上述指定的7个字段，不要添加其他字段

合同文本：
CONTRACT_TEXT_PLACEHOLDER

请返回JSON格式的提取结果，格式如下：
{
  "party_a": "甲方名称",
  "party_b": "乙方名称", 
  "contract_type": "合同方向或null",
  "contract_amount": 数字或null,
  "project_description": "合同内容描述",
  "positions": "岗位信息",
  "personnel_list": "相关人员清单"
}
"""
        return base_template
    
    def _call_qwen_api(self, prompt: str) -> str:
        """
        调用Qwen API
        
        Args:
            prompt: 发送给API的提示词
        
        Returns:
            API返回的文本内容
        
        Raises:
            Exception: API调用失败时抛出异常
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的合同分析专家，擅长从合同文本中提取结构化信息。请严格按照要求的JSON格式返回结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": 0.1,
                "max_tokens": 2000,
                "top_p": 0.9
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if "output" in result and "text" in result["output"]:
                        return result["output"]["text"].strip()
                    else:
                        raise Exception(f"API响应格式错误: {result}")
                elif response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                        print(f"API调用频率限制，等待{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception("API调用频率限制，重试次数已用完")
                else:
                    error_msg = f"API调用失败，状态码: {response.status_code}, 响应: {response.text}"
                    if attempt < self.max_retries - 1:
                        print(f"API错误，重试中... 错误信息: {error_msg}")
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
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"未知错误，重试中... 错误信息: {str(e)}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise Exception(f"API调用失败: {str(e)}")
        
        raise Exception("API调用失败，已达到最大重试次数")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析API返回的JSON响应
        
        Args:
            response_text: API返回的文本
        
        Returns:
            解析后的字典对象
        
        Raises:
            Exception: JSON解析失败时抛出异常
        """
        print(f"原始LLM响应: {response_text[:500]}...")  # 打印前500字符用于调试
        
        try:
            # 尝试直接解析JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            try:
                # 清理响应文本，移除可能的前缀和后缀
                cleaned_text = response_text.strip()
                
                # 查找JSON开始和结束位置
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = cleaned_text[start_idx:end_idx]
                    print(f"提取的JSON字符串: {json_str[:200]}...")  # 打印提取的JSON用于调试
                    return json.loads(json_str)
                else:
                    raise Exception("响应中未找到有效的JSON格式")
            except json.JSONDecodeError as e:
                # 尝试更激进的清理方法
                try:
                    # 移除可能的markdown代码块标记
                    if '```json' in response_text:
                        start_marker = response_text.find('```json') + 7
                        end_marker = response_text.find('```', start_marker)
                        if end_marker != -1:
                            json_str = response_text[start_marker:end_marker].strip()
                            print(f"从markdown提取的JSON: {json_str[:200]}...")  # 调试信息
                            return json.loads(json_str)
                    
                    # 如果还是失败，尝试逐行查找JSON
                    lines = response_text.split('\n')
                    json_lines = []
                    in_json = False
                    brace_count = 0
                    
                    for line in lines:
                        if '{' in line and not in_json:
                            in_json = True
                            brace_count += line.count('{') - line.count('}')
                            json_lines.append(line)
                        elif in_json:
                            brace_count += line.count('{') - line.count('}')
                            json_lines.append(line)
                            if brace_count <= 0:
                                break
                    
                    if json_lines:
                        json_str = '\n'.join(json_lines)
                        print(f"逐行提取的JSON: {json_str[:200]}...")  # 调试信息
                        return json.loads(json_str)
                    
                    raise Exception(f"所有JSON提取方法都失败了")
                    
                except json.JSONDecodeError as e2:
                    raise Exception(f"JSON解析失败: {str(e2)}\n原始响应: {response_text[:1000]}")
    
    def _validate_and_clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和清理提取的元数据
        
        Args:
            metadata: 原始元数据字典
        
        Returns:
            清理后的元数据字典
        """
        # 定义精简的字段列表（只保留用户要求的6个字段）
        required_fields = [
            'party_a', 'party_b', 'contract_type', 'contract_amount',
            'project_description', 'positions', 'personnel_list'
        ]
        
        # 创建清理后的字典
        cleaned_metadata = {}
        
        # 确保所有字段都存在
        for field in required_fields:
            cleaned_metadata[field] = metadata.get(field, None)
        
        # 验证合同类型（现在接受任何字符串值，如'金融方向', '互联网方向', '电信方向', '其他'等）
        # 不再限制为特定值，允许更灵活的合同方向分类
        
        # 验证合同金额
        if cleaned_metadata['contract_amount']:
            try:
                cleaned_metadata['contract_amount'] = float(cleaned_metadata['contract_amount'])
            except (ValueError, TypeError):
                cleaned_metadata['contract_amount'] = None
        
        # 添加提取时间戳
        cleaned_metadata['extracted_at'] = datetime.now().isoformat()
        
        return cleaned_metadata
    
    def _generate_metadata_vector(self, metadata: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        为元数据生成向量
        
        Args:
            metadata: 元数据字典
        
        Returns:
            元数据向量，如果生成失败则返回None
        """
        if not self.vector_model:
            print("向量模型未加载，无法生成元数据向量")
            return None
        
        try:
            # 将元数据字段拼接成文本
            metadata_text_parts = []
            
            # 按重要性顺序拼接字段
            if metadata.get('party_a'):
                metadata_text_parts.append(f"甲方：{metadata['party_a']}")
            if metadata.get('party_b'):
                metadata_text_parts.append(f"乙方：{metadata['party_b']}")
            if metadata.get('contract_type'):
                metadata_text_parts.append(f"合同方向：{metadata['contract_type']}")
            if metadata.get('contract_amount'):
                metadata_text_parts.append(f"合同金额：{metadata['contract_amount']}元")
            if metadata.get('project_description'):
                metadata_text_parts.append(f"项目描述：{metadata['project_description']}")
            if metadata.get('positions'):
                metadata_text_parts.append(f"岗位信息：{metadata['positions']}")
            if metadata.get('personnel_list'):
                metadata_text_parts.append(f"人员清单：{metadata['personnel_list']}")
            
            # 拼接成完整文本
            metadata_text = " ".join(metadata_text_parts)
            
            if not metadata_text.strip():
                print("元数据为空，无法生成向量")
                return None
            
            # 生成向量
            vector = self.vector_model.encode(metadata_text)
            print(f"成功生成元数据向量，维度：{vector.shape}")
            return vector
            
        except Exception as e:
            print(f"生成元数据向量失败: {e}")
            return None
    
    def extract_metadata(self, contract_text: str, contract_type: str = "unknown") -> Tuple[Dict[str, Any], Optional[np.ndarray]]:
        """
        从合同文本中提取元数据并生成向量
        
        Args:
            contract_text: 合同文本内容
            contract_type: 预期的合同方向，如"金融方向"、"互联网方向"、"电信方向"、"其他"或"unknown"
        
        Returns:
            元组：(包含提取元数据的字典, 元数据向量)
        
        Raises:
            Exception: 提取过程中发生错误时抛出异常
        """
        if not contract_text or not contract_text.strip():
            raise ValueError("合同文本不能为空")
        
        try:
            # 获取Prompt模板
            prompt_template = self._get_prompt_template(contract_type)
            prompt = prompt_template.replace('CONTRACT_TEXT_PLACEHOLDER', contract_text)
            
            # 调用Qwen API
            response_text = self._call_qwen_api(prompt)
            
            # 解析JSON响应
            metadata = self._parse_json_response(response_text)
            
            # 验证和清理元数据
            cleaned_metadata = self._validate_and_clean_metadata(metadata)
            
            # 生成元数据向量
            metadata_vector = self._generate_metadata_vector(cleaned_metadata)
            
            result = {
                'success': True,
                'metadata': cleaned_metadata,
                'raw_response': response_text
            }
            
            return result, metadata_vector
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'metadata': None,
                'raw_response': None
            }
            return error_result, None

# 使用示例
if __name__ == "__main__":
    # 测试代码
    extractor = MetadataExtractor()
    
    # 示例合同文本
    sample_contract = """
    软件开发外包合同
    
    甲方：北京科技有限公司
    乙方：上海软件开发有限公司
    
    根据《中华人民共和国合同法》等相关法律法规，甲乙双方就软件开发项目达成如下协议：
    
    一、项目内容
    乙方为甲方开发一套客户管理系统，包括用户管理、订单管理、报表统计等功能模块。
    
    二、合同金额
    本项目总金额为人民币50万元整。
    
    三、项目周期
    项目开始时间：2024年1月1日
    项目结束时间：2024年6月30日
    
    四、付款方式
    项目启动后支付30%，中期验收后支付40%，最终验收后支付30%。
    
    合同签订日期：2023年12月15日
    """
    
    result = extractor.extract_metadata(sample_contract)
    print(json.dumps(result, ensure_ascii=False, indent=2))