"""
清理脚本：删除所有已上传的PDF文件和对应的向量数据

此脚本会删除：
1. uploaded_contracts 目录下的所有PDF文件
2. Elasticsearch contracts_unified 索引中的所有文档
3. Elasticsearch contract_upload_status 索引中的所有上传状态记录

使用方法:
    python cleanup_all_data.py          # 交互式确认
    python cleanup_all_data.py --yes    # 跳过确认直接删除
"""

import os
import sys
import argparse
from pathlib import Path
from elasticsearch import Elasticsearch


def delete_all_pdfs(upload_dir: Path) -> dict:
    """删除上传目录中的所有PDF文件"""
    deleted_files = []
    errors = []
    
    if not upload_dir.exists():
        return {
            "deleted_count": 0,
            "deleted_files": [],
            "errors": [],
            "message": f"目录不存在: {upload_dir}"
        }
    
    for pdf_file in upload_dir.glob("*.pdf"):
        try:
            pdf_file.unlink()
            deleted_files.append(pdf_file.name)
            print(f"  已删除: {pdf_file.name}")
        except Exception as e:
            errors.append({"file": pdf_file.name, "error": str(e)})
            print(f"  删除失败: {pdf_file.name} - {e}")
    
    return {
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files,
        "errors": errors
    }


def delete_all_documents(es: Elasticsearch, index_name: str) -> dict:
    """删除Elasticsearch索引中的所有文档"""
    try:
        # 检查索引是否存在
        if not es.indices.exists(index=index_name):
            return {
                "deleted_count": 0,
                "message": f"索引不存在: {index_name}"
            }
        
        # 获取文档总数
        count_response = es.count(index=index_name)
        total_docs = count_response.get("count", 0)
        
        if total_docs == 0:
            return {
                "deleted_count": 0,
                "message": f"索引 {index_name} 中没有文档"
            }
        
        # 删除所有文档
        result = es.delete_by_query(
            index=index_name,
            body={"query": {"match_all": {}}},
            conflicts="proceed",
            refresh=True
        )
        
        deleted_count = result.get("deleted", 0)
        
        return {
            "deleted_count": deleted_count,
            "total_before": total_docs,
            "message": f"成功从 {index_name} 删除 {deleted_count} 条记录"
        }
        
    except Exception as e:
        return {
            "deleted_count": 0,
            "error": str(e),
            "message": f"删除索引 {index_name} 中的文档失败: {e}"
        }


def main():
    parser = argparse.ArgumentParser(description="清理所有上传的PDF文件和向量数据")
    parser.add_argument("--yes", "-y", action="store_true", 
                        help="跳过确认对话，直接执行删除")
    args = parser.parse_args()

    print("=" * 60)
    print("开始清理所有上传的PDF文件和向量数据...")
    print("=" * 60)
    
    # 配置路径
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    upload_dir = project_root / "uploaded_contracts"
    
    # Elasticsearch 配置
    es_host = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
    contracts_index = "contracts_unified"
    status_index = "contract_upload_status"
    
    print(f"\n上传目录: {upload_dir}")
    print(f"Elasticsearch: {es_host}")
    print(f"合同数据索引: {contracts_index}")
    print(f"上传状态索引: {status_index}")
    
    # 确认操作
    if not args.yes:
        print("\n" + "=" * 60)
        print("警告: 此操作将永久删除所有数据，且无法恢复！")
        print("=" * 60)
        confirm = input("\n请输入 'YES' 确认删除所有数据: ")
        
        if confirm.strip() != "YES":
            print("\n操作已取消。")
            sys.exit(0)
    else:
        print("\n使用 --yes 参数，跳过确认...")
    
    print("\n" + "-" * 60)
    print("步骤 1/3: 删除PDF文件...")
    print("-" * 60)
    pdf_result = delete_all_pdfs(upload_dir)
    print(f"\n删除了 {pdf_result['deleted_count']} 个PDF文件")
    if pdf_result.get("errors"):
        print(f"发生 {len(pdf_result['errors'])} 个错误")
    
    # 连接 Elasticsearch
    try:
        es = Elasticsearch(
            [es_host], 
            headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
        )
        
        if not es.ping():
            print("\n错误: 无法连接到Elasticsearch")
            sys.exit(1)
        print("\n已连接到Elasticsearch")
        
    except Exception as e:
        print(f"\n错误: 连接Elasticsearch失败: {e}")
        sys.exit(1)
    
    print("\n" + "-" * 60)
    print("步骤 2/3: 删除合同向量数据...")
    print("-" * 60)
    contracts_result = delete_all_documents(es, contracts_index)
    print(contracts_result.get("message", ""))
    
    print("\n" + "-" * 60)
    print("步骤 3/3: 删除上传状态记录...")
    print("-" * 60)
    status_result = delete_all_documents(es, status_index)
    print(status_result.get("message", ""))
    
    # 汇总
    print("\n" + "=" * 60)
    print("清理完成！汇总信息：")
    print("=" * 60)
    print(f"  PDF文件: 删除了 {pdf_result['deleted_count']} 个")
    print(f"  合同向量数据: 删除了 {contracts_result['deleted_count']} 条")
    print(f"  上传状态记录: 删除了 {status_result['deleted_count']} 条")
    print("\n现在可以重新上传PDF文件了。")


if __name__ == "__main__":
    main()
