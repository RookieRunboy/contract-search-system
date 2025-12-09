import requests
import json
import time
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
import os
from pathlib import Path
import numpy as np

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

from document_processor import DocumentProcessor
from embedding_client import RemoteEmbeddingClient
from customer_category_loader import CustomerCategoryLookup

class MetadataExtractor:
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化元数据提取器

        Args:
            api_key: DeepSeek API密钥，如果不提供则尝试从环境变量读取
        """
        self.api_key = api_key or os.getenv("CONTRACT_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("警告: 未检测到 DeepSeek API 密钥（请设置 CONTRACT_API_KEY），LLM 元数据提取将被跳过。")
        self.api_url = "http://model.aicc.chinasoftinc.com/v1/chat/completions"
        self.model = "DeepSeekV3"
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        
        # 初始化向量服务（与正文内容使用相同的模型）
        try:
            self.vector_client = RemoteEmbeddingClient(model="bge-m3")
            print("向量服务初始化成功")
        except Exception as e:
            print(f"向量服务初始化失败: {e}")
            self.vector_client = None

        mapping_path_env = os.getenv("CUSTOMER_CATEGORY_MAPPING_PATH")
        if mapping_path_env:
            mapping_path = Path(mapping_path_env).expanduser()
        elif DEFAULT_CUSTOMER_CATEGORY_PATH.exists():
            mapping_path = DEFAULT_CUSTOMER_CATEGORY_PATH
        else:
            mapping_path = None

        if mapping_path:
            print(f"使用客户分类白名单: {mapping_path}")
            mapping_path_str: Optional[str] = str(mapping_path)
        else:
            print(
                "提示: 未检测到客户分类白名单文件，客户分类元数据将保持为空。"
                " 可通过环境变量 CUSTOMER_CATEGORY_MAPPING_PATH 指定 Excel 路径。"
            )
            mapping_path_str = None

        self.customer_category_lookup = CustomerCategoryLookup(mapping_path_str)
        self._customer_category_lookup_enabled = mapping_path_str is not None
        self._unmatched_customer_names: Set[str] = set()
    
    def _get_prompt_template(self, contract_type: str = "unknown") -> str:
        """
        根据合同类型获取相应的Prompt模板

        Args:
            contract_type: 合同方向，"金融方向"、"互联网方向"、"电信方向"或"其他"

        Returns:
            格式化的Prompt字符串
        """

        entity_list_text = "\n".join(f"- {name}" for name in CHINASOFT_ENTITY_NAMES)

        base_template = f"""
你是一个专业的合同分析助手。请仔细分析以下合同文本，并提取关键信息。

必须提取的字段：
- customer_name: 客户名称（通常对应甲方；如存在多个客户，仅输出主要客户）
- our_entity: 中软国际在合同中的实体名称（仅限以下名单；若未提及请输出null）
- contract_type: 合同方向（金融方向【银行、保险、证券】、互联网方向、电信方向、其他）
- contract_amount: 合同金额（数字，如果有多个金额取总金额）
- signing_date: 合同签订日期（YYYY-MM-DD格式）
- project_description: 合同内容（项目描述或服务内容）
- positions: 岗位信息
- personnel_list: 相关人员清单

中软国际实体名单如下：
{entity_list_text}

提取规则：
1. 仔细阅读合同全文，确保字段准确。
2. 如果合同为三方协议且中软国际被标注为丙方、第三方或类似角色，仅保留甲方对应的客户名称。
3. 如果未在合同中找到名单内的中软国际实体，请将our_entity设置为null。
4. 金额请提取数字部分，不包含货币符号。
5. 签订日期请提取为YYYY-MM-DD格式，如2024-01-15。
6. 返回结果必须是有效的JSON格式，且只包含上述8个字段。
7. 若某个字段缺失，请显式写明null。

合同文本：
CONTRACT_TEXT_PLACEHOLDER

请返回JSON格式的提取结果，格式如下：
{{
  "customer_name": "客户名称或null",
  "our_entity": "中软国际实体或null",
  "contract_type": "合同方向或null",
  "contract_amount": 数字或null,
  "signing_date": "YYYY-MM-DD或null",
  "project_description": "合同内容描述或null",
  "positions": "岗位信息或null",
  "personnel_list": "相关人员清单或null"
}}
"""
        return base_template
    
    def _call_llm_api(self, prompt: str) -> str:
        """
        调用DeepSeek API
        
        Args:
            prompt: 发送给API的提示词
        
        Returns:
            API返回的文本内容
        
        Raises:
            Exception: API调用失败时抛出异常
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
                    "content": "你是一个专业的合同分析专家，擅长从合同文本中提取结构化信息。请严格按照要求的JSON格式返回结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
            "top_p": 0.95,
            "stream": False
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    choices = result.get("choices")
                    if choices and isinstance(choices, list):
                        message = choices[0].get("message", {})
                        content = message.get("content")
                        if content:
                            return content.strip()
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
        # 定义精简的字段列表（包含用户要求的8个字段）
        required_fields = [
            'customer_name',
            'our_entity',
            'contract_type',
            'customer_category_level1',
            'customer_category_level2',
            'contract_amount',
            'signing_date',
            'project_description',
            'positions',
            'personnel_list',
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

        cleaned_metadata['customer_name'] = self._normalize_customer_name(cleaned_metadata.get('customer_name'))
        cleaned_metadata['our_entity'] = self._normalize_chinasoft_entity(cleaned_metadata.get('our_entity'))

        self._enrich_customer_category(cleaned_metadata)

        # 添加提取时间戳
        cleaned_metadata['extracted_at'] = datetime.now().isoformat()

        return cleaned_metadata

    def _normalize_customer_name(self, value: Any) -> Optional[str]:
        """标准化客户名称，去除我方实体并优先返回甲方"""
        if value is None:
            return None

        raw_items: List[Any]
        if isinstance(value, list):
            raw_items = value
        else:
            raw_items = [value]

        candidates: List[str] = []
        for item in raw_items:
            normalized = self._coerce_non_empty_text(item)
            if not normalized:
                continue

            parts = re.split(r'[，,、;；/\n]+', normalized)
            for part in parts:
                candidate = part.strip()
                if not candidate:
                    continue
                candidate = re.sub(r'^[甲乙丙丁]方[:：\s]*', '', candidate)
                candidate = re.sub(r'^客户[:：\s]*', '', candidate)
                candidate = candidate.strip("（）() ")
                if candidate:
                    candidates.append(candidate)

        if not candidates:
            return None

        filtered: List[str] = []
        seen: set[str] = set()
        for name in candidates:
            if any(entity in name for entity in CHINASOFT_ENTITY_NAMES):
                continue
            if name not in seen:
                seen.add(name)
                filtered.append(name)

        if filtered:
            return filtered[0]

        return candidates[0]

    def _normalize_chinasoft_entity(self, value: Any) -> Optional[str]:
        """将我方实体归一化为预设名单中的名称"""
        if value is None:
            return None

        raw_items: List[Any]
        if isinstance(value, list):
            raw_items = value
        else:
            raw_items = [value]

        candidates: List[str] = []
        for item in raw_items:
            normalized = self._coerce_non_empty_text(item)
            if not normalized:
                continue

            parts = re.split(r'[，,、;；/\n]+', normalized)
            if not parts:
                parts = [normalized]

            for part in parts:
                candidate = part.strip()
                candidate = re.sub(r'^[甲乙丙丁]方[:：\s]*', '', candidate)
                candidate = candidate.strip("（）() ")
                if candidate:
                    candidates.append(candidate)

        for name in candidates:
            for entity in CHINASOFT_ENTITY_NAMES:
                if entity in name:
                    return entity

        for name in candidates:
            if '中软国际' in name or 'Chinasoft' in name:
                return name

        return None

    def _enrich_customer_category(self, metadata: Dict[str, Any]) -> None:
        """根据客户名称补齐客户一级/二级分类，并清理旧字段。"""
        customer_name = metadata.get('customer_name')

        if not customer_name:
            level1 = None
            level2 = None
        else:
            level1, level2 = self.customer_category_lookup.lookup(customer_name)

        metadata['customer_category_level1'] = level1
        metadata['customer_category_level2'] = level2

        if (
            level1 is None
            and level2 is None
            and customer_name
            and self._customer_category_lookup_enabled
            and customer_name not in self._unmatched_customer_names
        ):
            print(f"客户分类白名单未匹配：{customer_name}")
            self._unmatched_customer_names.add(customer_name)

        metadata['contract_type'] = None
    
    def _generate_metadata_vector(self, metadata: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        为元数据生成向量
        
        Args:
            metadata: 元数据字典
        
        Returns:
            元数据向量，如果生成失败则返回None
        """
        if not self.vector_client:
            print("向量服务未初始化，无法生成元数据向量")
            return None
        
        try:
            # 将元数据字段拼接成文本
            metadata_text_parts = []
            
            # 按重要性顺序拼接字段
            if metadata.get('customer_name'):
                metadata_text_parts.append(f"客户名称：{metadata['customer_name']}")
            if metadata.get('our_entity'):
                metadata_text_parts.append(f"中软国际实体：{metadata['our_entity']}")
            category_parts = [
                part for part in (
                    metadata.get('customer_category_level1'),
                    metadata.get('customer_category_level2'),
                )
                if part
            ]
            if category_parts:
                metadata_text_parts.append(f"客户分类：{' / '.join(category_parts)}")
            if metadata.get('contract_amount'):
                metadata_text_parts.append(f"合同金额：{metadata['contract_amount']}元")
            if metadata.get('signing_date'):
                metadata_text_parts.append(f"签订日期：{metadata['signing_date']}")
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
            vector_results = self.vector_client.embed(metadata_text)
            if not vector_results:
                print("向量服务返回空结果，无法生成向量")
                return None

            vector = np.asarray(vector_results[0], dtype=float)
            print(f"成功生成元数据向量，维度：{vector.shape}")
            return vector
            
        except Exception as e:
            print(f"生成元数据向量失败: {e}")
            return None
    
    def _extract_metadata_core(
        self,
        contract_text: str,
        contract_type: str = "unknown",
    ) -> Tuple[Dict[str, Any], str]:
        """执行一次LLM调用并返回清理后的元数据与原始响应"""
        if not contract_text or not contract_text.strip():
            raise ValueError("合同文本不能为空")

        prompt_template = self._get_prompt_template(contract_type)
        prompt = prompt_template.replace("CONTRACT_TEXT_PLACEHOLDER", contract_text)

        response_text = self._call_llm_api(prompt)
        metadata = self._parse_json_response(response_text)
        cleaned_metadata = self._validate_and_clean_metadata(metadata)
        return cleaned_metadata, response_text

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
        if not self.api_key:
            message = "DeepSeek API 密钥未配置（请设置环境变量 CONTRACT_API_KEY），已跳过 LLM 元数据提取。"
            print(message)
            error_result = {
                'success': False,
                'error': message,
                'metadata': None,
                'raw_response': None
            }
            return error_result, None

        try:
            cleaned_metadata, response_text = self._extract_metadata_core(contract_text, contract_type)
            
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

    def extract_metadata_from_long_text(
        self,
        full_text: str,
        contract_type: str = "unknown",
        chunk_size: int = 2500,
        chunk_overlap: int = 250,
    ) -> Tuple[Dict[str, Any], Optional[np.ndarray]]:
        """通过分块与合并流程提取长文本的元数据"""
        if not full_text or not full_text.strip():
            raise ValueError("合同文本不能为空")

        if not self.api_key:
            message = "DeepSeek API 密钥未配置（请设置环境变量 CONTRACT_API_KEY），已跳过 LLM 元数据提取。"
            print(message)
            error_result = {
                'success': False,
                'error': message,
                'metadata': None,
                'raw_response': None
            }
            return error_result, None

        processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = processor._split_text_into_chunks(full_text, chunk_size, chunk_overlap)

        if not chunks:
            return self.extract_metadata(full_text, contract_type)

        if len(chunks) == 1:
            return self.extract_metadata(full_text, contract_type)

        metadata_results: List[Dict[str, Any]] = []
        raw_responses: List[str] = []
        partial_errors: List[str] = []

        for index, chunk in enumerate(chunks, start=1):
            try:
                chunk_metadata, chunk_raw = self._extract_metadata_core(chunk, contract_type)
                metadata_results.append(chunk_metadata)
                raw_responses.append(f"Chunk {index}:\n{chunk_raw}")
            except Exception as exc:  # noqa: BLE001 - 捕获单块异常并继续
                error_message = f"第 {index} 块提取失败: {exc}"
                print(error_message)
                partial_errors.append(error_message)

        if not metadata_results:
            joined_errors = "; ".join(partial_errors) if partial_errors else "未知错误"
            error_result = {
                'success': False,
                'error': f"所有文本块的元数据提取均失败: {joined_errors}",
                'metadata': None,
                'raw_response': None,
                'chunks_processed': len(chunks),
                'chunks_succeeded': 0
            }
            return error_result, None

        merged_metadata = self._merge_metadata_results(metadata_results)
        metadata_vector = self._generate_metadata_vector(merged_metadata)

        result: Dict[str, Any] = {
            'success': True,
            'metadata': merged_metadata,
            'raw_response': "\n\n".join(raw_responses) if raw_responses else None,
            'chunks_processed': len(chunks),
            'chunks_succeeded': len(metadata_results)
        }

        if partial_errors:
            result['partial_errors'] = partial_errors

        return result, metadata_vector

    def _merge_metadata_results(self, metadata_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """根据预设规则合并多个元数据结果"""
        required_fields = [
            'customer_name',
            'our_entity',
            'customer_category_level1',
            'customer_category_level2',
            'contract_type',
            'contract_amount',
            'signing_date',
            'project_description',
            'positions',
            'personnel_list',
        ]

        merged_metadata = {field: None for field in required_fields}

        if not metadata_results:
            merged_metadata['extracted_at'] = datetime.now().isoformat()
            return merged_metadata

        first_value_fields = [
            'customer_name',
            'our_entity',
            'customer_category_level1',
            'customer_category_level2',
            'contract_type',
        ]
        for field in first_value_fields:
            for item in metadata_results:
                value = self._coerce_non_empty_text(item.get(field))
                if value is not None:
                    merged_metadata[field] = value
                    break

        # 签订日期单独处理，确保格式
        for item in metadata_results:
            normalized_date = self._normalize_signing_date(item.get('signing_date'))
            if normalized_date:
                merged_metadata['signing_date'] = normalized_date
                break

        merged_metadata['contract_amount'] = self._select_contract_amount(metadata_results)

        text_concat_fields = ['project_description', 'positions', 'personnel_list']
        for field in text_concat_fields:
            merged_metadata[field] = self._merge_text_field(metadata_results, field)

        merged_metadata['customer_name'] = self._normalize_customer_name(merged_metadata.get('customer_name'))
        merged_metadata['our_entity'] = self._normalize_chinasoft_entity(merged_metadata.get('our_entity'))
        merged_metadata['extracted_at'] = datetime.now().isoformat()
        return merged_metadata

    def _select_contract_amount(self, metadata_results: List[Dict[str, Any]]) -> Optional[float]:
        """选择最可信的合同金额（最大值优先）"""
        max_amount: Optional[float] = None
        for item in metadata_results:
            normalized_amount = self._normalize_contract_amount(item.get('contract_amount'))
            if normalized_amount is None:
                continue
            if max_amount is None or normalized_amount > max_amount:
                max_amount = normalized_amount
        return max_amount

    def _normalize_contract_amount(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned or cleaned.lower() == 'null':
                return None
            cleaned = cleaned.replace(',', '')
            match = re.search(r"[-+]?\d*\.?\d+", cleaned)
            if match:
                try:
                    return float(match.group())
                except ValueError:
                    return None
        return None

    def _normalize_signing_date(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate or candidate.lower() == 'null':
                return None

            normalized = candidate
            normalized = normalized.replace('年', '-').replace('月', '-').replace('日', '')
            normalized = normalized.replace('/', '-').replace('.', '-')

            patterns = ['%Y-%m-%d', '%Y-%m', '%Y%m%d']
            for pattern in patterns:
                try:
                    dt = datetime.strptime(normalized, pattern)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            if re.match(r'^\d{4}-\d{2}-\d{2}$', normalized):
                return normalized

        return None

    def _merge_text_field(self, metadata_results: List[Dict[str, Any]], field: str) -> Optional[str]:
        seen: set[str] = set()
        merged_parts: List[str] = []

        for item in metadata_results:
            value = item.get(field)
            if value is None:
                continue

            if isinstance(value, list):
                candidates = [self._coerce_non_empty_text(v) for v in value]
                normalized_values = [v for v in candidates if v]
            else:
                normalized = self._coerce_non_empty_text(value)
                normalized_values = [normalized] if normalized else []

            for normalized_value in normalized_values:
                if normalized_value not in seen:
                    seen.add(normalized_value)
                    merged_parts.append(normalized_value)

        if not merged_parts:
            return None

        return "\n".join(merged_parts)

    def _coerce_non_empty_text(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return str(value).strip() or None

# 使用示例
if __name__ == "__main__":
    # 测试代码
    extractor = MetadataExtractor()
    
    # 示例合同文本
    sample_contract = """
    软件开发外包合同
    
    甲方：北京科技有限公司
    乙方：北京中软国际信息技术有限公司
    
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
