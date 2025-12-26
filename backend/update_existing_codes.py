"""
批量更新已存在文档的合同编码和CIR编码到Elasticsearch metadata中

使用方法:
    python update_existing_codes.py

此脚本会：
1. 获取所有已存在的合同文档
2. 从文件名中提取合同编码和CIR编码
3. 更新每个文档的 document_metadata 字段
"""

import re
import json
from pathlib import Path
from typing import Dict, Optional, Any, List
import requests
from dotenv import load_dotenv
import os

# 加载环境变量
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ELASTICSEARCH_INDEX", "contracts_unified")


def _extract_codes_from_filename(filename: str) -> Dict[str, Optional[str]]:
    """
    从文件名中提取合同编码和CIR编码。
    
    支持的命名模式：
    1. [合同编码]-[CIR编码]合同名.pdf (方括号格式)
    2. [合同编码]合同名.pdf
    3. [CIR编码]合同名.pdf
    4. 合同编码-CIR编码-合同名.pdf (无方括号格式)
    5. 合同名.pdf (无编码)
    """
    result: Dict[str, Optional[str]] = {
        "contract_code": None,
        "cir_code": None,
    }
    
    if not filename:
        return result
    
    base_name = Path(filename).stem
    
    cir_pattern = re.compile(r'^cir\d+$', re.IGNORECASE)
    contract_code_pattern = re.compile(r'^[A-Za-z]\d+$')
    
    def classify_code(code: str) -> str:
        code_stripped = code.strip()
        if cir_pattern.match(code_stripped):
            return 'cir'
        if contract_code_pattern.match(code_stripped):
            return 'contract'
        return 'unknown'
    
    def assign_code(code: str) -> None:
        code_type = classify_code(code)
        if code_type == 'cir':
            result["cir_code"] = code
        elif code_type == 'contract':
            result["contract_code"] = code
    
    # 模式A: 方括号格式 [Code1]-[Code2]Name
    pattern_two_brackets = r'^\[([^\]]+)\]-\[([^\]]+)\]'
    match_two_brackets = re.match(pattern_two_brackets, base_name)
    if match_two_brackets:
        assign_code(match_two_brackets.group(1).strip())
        assign_code(match_two_brackets.group(2).strip())
        return result
    
    # 模式B: 方括号格式 [Code]Name
    pattern_one_bracket = r'^\[([^\]]+)\]'
    match_one_bracket = re.match(pattern_one_bracket, base_name)
    if match_one_bracket:
        assign_code(match_one_bracket.group(1).strip())
        return result
    
    # 模式C: 无方括号格式 - 用连字符分隔
    parts = base_name.split('-')
    if len(parts) >= 2:
        for part in parts[:2]:
            part_stripped = part.strip()
            if part_stripped:
                assign_code(part_stripped)
        
        if result["contract_code"] is not None or result["cir_code"] is not None:
            return result
    
    return result


def test_connection() -> bool:
    """测试 ES 连接"""
    try:
        response = requests.get(ES_HOST, timeout=5)
        if response.status_code == 200:
            print(f"已连接到 Elasticsearch {response.json().get('version', {}).get('number')}")
            return True
        else:
            print(f"连接失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"连接失败: {e}")
        return False


def get_all_contract_names() -> List[str]:
    """获取所有唯一的合同名称"""
    agg_query = {
        "size": 0,
        "aggs": {
            "contracts": {
                "terms": {
                    "field": "contractName",
                    "size": 10000
                }
            }
        }
    }
    
    response = requests.get(
        f"{ES_HOST}/{ES_INDEX}/_search",
        json=agg_query,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"查询失败: {response.status_code} - {response.text}")
    
    result = response.json()
    buckets = result.get("aggregations", {}).get("contracts", {}).get("buckets", [])
    return [b["key"] for b in buckets]


def update_document_codes(contract_name: str, codes: Dict[str, Optional[str]]) -> int:
    """更新指定合同的所有页面文档的编码字段"""
    
    update_script = """
        if (ctx._source.document_metadata == null) {
            ctx._source.document_metadata = new HashMap();
        }
        ctx._source.document_metadata.contract_code = params.contract_code;
        ctx._source.document_metadata.cir_code = params.cir_code;
    """
    
    update_query = {
        "script": {
            "source": update_script,
            "lang": "painless",
            "params": {
                "contract_code": codes.get("contract_code"),
                "cir_code": codes.get("cir_code")
            }
        },
        "query": {
            "term": {
                "contractName": contract_name
            }
        }
    }
    
    response = requests.post(
        f"{ES_HOST}/{ES_INDEX}/_update_by_query?refresh=true",
        json=update_query,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    if response.status_code not in [200, 201]:
        print(f"  警告: 更新 {contract_name} 失败: {response.status_code}")
        return 0
    
    return response.json().get("updated", 0)


def main():
    print(f"连接 Elasticsearch: {ES_HOST}")
    
    if not test_connection():
        return
    
    print(f"使用索引: {ES_INDEX}")
    
    # 检查索引是否存在
    response = requests.get(f"{ES_HOST}/{ES_INDEX}", timeout=5)
    if response.status_code != 200:
        print(f"错误: 索引 {ES_INDEX} 不存在")
        return
    
    # 获取所有合同名称
    print("获取现有合同列表...")
    try:
        contract_names = get_all_contract_names()
    except Exception as e:
        print(f"获取合同列表失败: {e}")
        return
    
    print(f"找到 {len(contract_names)} 个合同")
    
    # 统计
    updated_count = 0
    with_code_count = 0
    
    for i, contract_name in enumerate(contract_names, 1):
        # 使用合同名作为"文件名"来提取编码
        filename = f"{contract_name}.pdf"
        codes = _extract_codes_from_filename(filename)
        
        has_code = codes["contract_code"] is not None or codes["cir_code"] is not None
        
        if has_code:
            with_code_count += 1
            if i <= 20 or i % 50 == 0:  # 只打印前20个和每隔50个
                print(f"[{i}/{len(contract_names)}] {contract_name[:60]}...")
                print(f"  -> contract_code: {codes['contract_code']}, cir_code: {codes['cir_code']}")
        
        # 更新文档
        try:
            updated = update_document_codes(contract_name, codes)
            updated_count += updated
        except Exception as e:
            print(f"  更新失败: {e}")
        
        if i % 100 == 0:
            print(f"进度: {i}/{len(contract_names)} 合同已处理")
    
    print("\n" + "=" * 50)
    print(f"完成! 共处理 {len(contract_names)} 个合同")
    print(f"  - 包含编码的合同: {with_code_count}")
    print(f"  - 无编码的合同: {len(contract_names) - with_code_count}")
    print(f"  - 更新的文档总数: {updated_count}")


if __name__ == "__main__":
    main()
