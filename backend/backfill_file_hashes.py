#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
backfill_file_hashes.py

一次性脚本：为历史上传的 PDF 文件计算并存储 SHA256 哈希值到 Elasticsearch。

使用方法：
    cd backend
    python backfill_file_hashes.py

功能：
1. 遍历 uploaded_contracts 目录中的所有 PDF 文件
2. 计算每个文件的 SHA256 哈希值
3. 更新对应 ES 文档的 document_metadata.file_hash 字段
4. 输出处理进度和统计信息
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 确保可以导入同目录的模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from elasticsearch import Elasticsearch, NotFoundError


def compute_file_hash(file_path: Path) -> str:
    """计算文件的 SHA256 哈希值。"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 分块读取大文件
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return f"sha256:{sha256_hash.hexdigest()}"


def get_es_client() -> Elasticsearch:
    """创建 Elasticsearch 客户端。"""
    es_host = os.getenv("ES_HOST", "http://localhost:9200")
    return Elasticsearch(
        [es_host],
        headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
    )


def find_es_document_id(
    es: Elasticsearch,
    index_name: str,
    contract_name: str
) -> Optional[str]:
    """查找合同的第一页文档 ID。"""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"contractName": contract_name}},
                    {"term": {"pageId": 1}}
                ]
            }
        },
        "_source": False,
        "size": 1
    }
    
    try:
        result = es.search(index=index_name, body=query)
        hits = result.get('hits', {}).get('hits', [])
        if hits:
            return hits[0]['_id']
    except Exception as e:
        print(f"  查询 ES 文档失败: {e}")
    
    return None


def update_document_hash(
    es: Elasticsearch,
    index_name: str,
    doc_id: str,
    file_hash: str
) -> bool:
    """更新 ES 文档中的 file_hash 字段。"""
    try:
        es.update(
            index=index_name,
            id=doc_id,
            body={
                "doc": {
                    "document_metadata.file_hash": file_hash
                }
            },
            retry_on_conflict=3
        )
        return True
    except Exception as e:
        print(f"  更新 ES 文档失败: {e}")
        return False


def update_with_script(
    es: Elasticsearch,
    index_name: str,
    doc_id: str,
    file_hash: str
) -> bool:
    """使用脚本更新嵌套字段 file_hash。"""
    try:
        es.update(
            index=index_name,
            id=doc_id,
            body={
                "script": {
                    "source": """
                        if (ctx._source.document_metadata == null) {
                            ctx._source.document_metadata = [:];
                        }
                        ctx._source.document_metadata.file_hash = params.file_hash;
                    """,
                    "lang": "painless",
                    "params": {
                        "file_hash": file_hash
                    }
                }
            },
            retry_on_conflict=3
        )
        return True
    except Exception as e:
        print(f"  脚本更新失败: {e}")
        return False


def main():
    print("=" * 60)
    print("文件哈希回填脚本")
    print("=" * 60)
    
    # 配置
    index_name = os.getenv("ES_INDEX", "contracts_unified")
    upload_dir = Path(__file__).resolve().parent.parent / "uploaded_contracts"
    
    if not upload_dir.exists():
        # 尝试 backend/uploaded_contracts
        upload_dir = Path(__file__).resolve().parent / "uploaded_contracts"
    
    if not upload_dir.exists():
        print(f"错误: 上传目录不存在: {upload_dir}")
        return 1
    
    print(f"上传目录: {upload_dir}")
    print(f"ES 索引: {index_name}")
    print()
    
    # 连接 ES
    try:
        es = get_es_client()
        if not es.ping():
            print("错误: 无法连接到 Elasticsearch")
            return 1
        print("✓ 已连接 Elasticsearch")
    except Exception as e:
        print(f"错误: 连接 Elasticsearch 失败: {e}")
        return 1
    
    # 检查索引是否存在
    if not es.indices.exists(index=index_name):
        print(f"错误: 索引 {index_name} 不存在")
        return 1
    
    print(f"✓ 索引 {index_name} 存在")
    print()
    
    # 遍历 PDF 文件
    pdf_files = list(upload_dir.glob("*.pdf")) + list(upload_dir.glob("*.PDF"))
    total_files = len(pdf_files)
    
    if total_files == 0:
        print("没有找到 PDF 文件")
        return 0
    
    print(f"找到 {total_files} 个 PDF 文件")
    print("-" * 60)
    
    # 统计
    stats = {
        "processed": 0,
        "updated": 0,
        "not_found": 0,
        "already_has_hash": 0,
        "errors": 0,
    }
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = pdf_path.name
        contract_name = pdf_path.stem
        
        print(f"[{idx}/{total_files}] {filename}")
        
        # 计算哈希
        try:
            file_hash = compute_file_hash(pdf_path)
            print(f"  哈希: {file_hash[:30]}...")
        except Exception as e:
            print(f"  计算哈希失败: {e}")
            stats["errors"] += 1
            continue
        
        # 查找 ES 文档
        doc_id = find_es_document_id(es, index_name, contract_name)
        if not doc_id:
            print(f"  ⚠ 未找到 ES 文档")
            stats["not_found"] += 1
            continue
        
        # 检查是否已有哈希值
        try:
            doc = es.get(index=index_name, id=doc_id, _source=["document_metadata"])
            existing_metadata = doc.get('_source', {}).get('document_metadata', {})
            existing_hash = existing_metadata.get('file_hash') if existing_metadata else None
            
            if existing_hash:
                if existing_hash == file_hash:
                    print(f"  ✓ 已有相同哈希值，跳过")
                    stats["already_has_hash"] += 1
                    stats["processed"] += 1
                    continue
                else:
                    print(f"  ⚠ 哈希值不同，更新中...")
        except Exception as e:
            print(f"  读取现有文档失败: {e}")
        
        # 更新哈希值
        success = update_with_script(es, index_name, doc_id, file_hash)
        if success:
            print(f"  ✓ 更新成功")
            stats["updated"] += 1
        else:
            stats["errors"] += 1
        
        stats["processed"] += 1
    
    # 输出统计
    print()
    print("=" * 60)
    print("处理完成！统计信息：")
    print(f"  总文件数: {total_files}")
    print(f"  已处理: {stats['processed']}")
    print(f"  已更新: {stats['updated']}")
    print(f"  已有哈希: {stats['already_has_hash']}")
    print(f"  未找到文档: {stats['not_found']}")
    print(f"  错误: {stats['errors']}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
