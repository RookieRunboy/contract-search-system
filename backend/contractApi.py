from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from pathlib import Path
import os

from pdfToElasticSearch import PdfToElasticsearch
from elasticSearchDelete import ElasticsearchDocumentDeleter
from elasticSearchSearch import ElasticsearchVectorSearch
from elasticsearch import exceptions as es_exceptions, helpers

# FastAPI应用
app = FastAPI(title="contractsSearchAPI")

FRONTEND_DIST_PATH = Path(__file__).resolve().parent.parent / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_PATH / "index.html"

if FRONTEND_INDEX_FILE.exists():
    assets_dir = FRONTEND_DIST_PATH / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")




# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建全局实例
pdf_to_es = PdfToElasticsearch()
es_deleter = ElasticsearchDocumentDeleter()
es_searcher = ElasticsearchVectorSearch()

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploaded_contracts"


def _format_file_size(size_in_bytes: int) -> str:
    """将文件大小格式化为可读字符串"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    size_in_kb = size_in_bytes / 1024
    if size_in_kb < 1024:
        return f"{size_in_kb:.1f} KB"
    size_in_mb = size_in_kb / 1024
    if size_in_mb < 1024:
        return f"{size_in_mb:.1f} MB"
    size_in_gb = size_in_mb / 1024
    return f"{size_in_gb:.2f} GB"


@app.get("/")
async def root():
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(FRONTEND_INDEX_FILE)

    return {
        "message": "contractsSearchAPI running",
        "version": "2.0.0",
        "endpoints": [
            "/document/add",
            "/document/delete",
            "/document/search",
            "/documents",
            "/documents/{document_name}",
            "/clear-index",
            "/system/elasticsearch",
            "/upload",
            "/search",
            "/health",
        ],
    }


@app.post("/document/add")
async def upload_document(file: UploadFile = File(...)):
    """
    上传PDF文档并索引到Elasticsearch
    """
    try:
        result= await run_in_threadpool(pdf_to_es.start_process, file)
        return {
            "code": 200,
            "message": "文档上传成功",
            "data": result
        }
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"文档上传失败: {str(e)}",
            "data": None
        }


# 兼容别名：POST /upload -> /document/add
@app.post("/upload")
async def upload_alias(file: UploadFile = File(...)):
    return await upload_document(file)


@app.delete("/document/delete")
async def delete_by_filename(filename: str = Query(..., description="要删除的文件名")):
    """
    根据文件名删除文档
    """
    try:
        result = await run_in_threadpool(es_deleter.delete_by_filename, filename)

        if result['status'] == 'success':
            return {
                "code": 200,
                "message": "文档删除成功",
                "data": result
            }
        else:
            return {
                "code": 500,
                "message": "文档删除失败",
                "data": result
            }
    except Exception as e:
        return {
            "code": 500,
            "message": f"文档删除异常: {str(e)}",
            "data": None
        }

@app.get("/document/search")
async def search_documents(
        query: str = Query(..., description="搜索关键词"),
        top_k: Optional[int] = Query(default=3, description="返回结果数量"),
        text_standard: Optional[int] = Query(default=3, description="标准文本权重"),
        text_ngram: Optional[int] = Query(default=1, description="N-gram文本权重"),
        vector_weight: Optional[float] = Query(default=5.0, description="向量权重"),
        fuzziness: Optional[str] = Query(default="AUTO", description="模糊匹配级别")
):
    """
    文档搜索接口
    """
    try:
        # 参数校验与边界保护
        if not query or not isinstance(query, str) or not query.strip():
            raise HTTPException(status_code=400, detail="query 为必填且不能为空")

        try:
            top_k_val = int(top_k) if top_k is not None else 3
        except Exception:
            raise HTTPException(status_code=400, detail="top_k 必须为整数")
        if top_k_val < 1 or top_k_val > 50:
            raise HTTPException(status_code=400, detail="top_k 取值范围为 1-50")

        try:
            ts_val = int(text_standard) if text_standard is not None else 3
            tn_val = int(text_ngram) if text_ngram is not None else 1
        except Exception:
            raise HTTPException(status_code=400, detail="text_standard 与 text_ngram 必须为整数")
        if ts_val < 0 or tn_val < 0:
            raise HTTPException(status_code=400, detail="文本权重必须为非负整数")

        try:
            vw_val = float(vector_weight) if vector_weight is not None else 5.0
        except Exception:
            raise HTTPException(status_code=400, detail="vector_weight 必须为数字")
        if vw_val < 0 or vw_val > 10:
            raise HTTPException(status_code=400, detail="vector_weight 取值范围为 0-10")

        if fuzziness not in ("AUTO", "0", "1", "2"):
            raise HTTPException(status_code=400, detail="fuzziness 仅支持 AUTO/0/1/2")

        results = await run_in_threadpool(
            es_searcher.search,
            query,
            top_k=top_k_val,
            text_standard=ts_val,
            text_ngram=tn_val,
            vector_weight=vw_val,
            fuzziness=fuzziness
        )

        return {
            "code": 200,
            "message": "搜索成功",
            "data": results
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"搜索异常: {str(e)}",
            "data": None
        }


# 兼容别名：GET /search -> /document/search
@app.get("/search")
async def search_alias(
        query: str = Query(..., description="搜索关键词"),
        top_k: Optional[int] = Query(default=3, description="返回结果数量"),
        text_standard: Optional[int] = Query(default=3, description="标准文本权重"),
        text_ngram: Optional[int] = Query(default=1, description="N-gram文本权重"),
        vector_weight: Optional[float] = Query(default=5.0, description="向量权重"),
        fuzziness: Optional[str] = Query(default="AUTO", description="模糊匹配级别")
):
    return await search_documents(
        query=query,
        top_k=top_k,
        text_standard=text_standard,
        text_ngram=text_ngram,
        vector_weight=vector_weight,
        fuzziness=fuzziness,
    )


# 系统信息接口
@app.get("/system/elasticsearch")
async def get_elasticsearch_info():
    """
    获取Elasticsearch系统信息
    """
    try:
        # 获取集群健康状态
        health = es_searcher.es.cluster.health()

        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "cluster_name": health.get('cluster_name'),
                "status": health.get('status'),
                "number_of_nodes": health.get('number_of_nodes'),
                "active_shards": health.get('active_shards'),
                "index_name": es_searcher.index_name
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取系统信息失败: {str(e)}",
            "data": None
        }


# 获取文档列表接口
@app.get("/documents")
async def get_uploaded_documents():
    """
    获取已上传的文档列表
    """
    try:
        index_name = es_searcher.index_name

        # 如果索引不存在，直接返回空列表
        if not es_searcher.es.indices.exists(index=index_name):
            return {
                "code": 200,
                "message": "索引不存在，已返回空列表",
                "total_documents": 0,
                "data": []
            }

        # 确保读取到最新数据
        es_searcher.es.indices.refresh(index=index_name)

        def build_query(field_name: str) -> dict:
            return {
                "size": 0,
                "aggs": {
                    "documents": {
                        "terms": {
                            "field": field_name,
                            "size": 1000
                        },
                        "aggs": {
                            "latest_upload": {
                                "max": {
                                    "field": "@timestamp"
                                }
                            }
                        }
                    }
                }
            }

        def execute_query(field_name: str):
            return es_searcher.es.search(
                index=index_name,
                body=build_query(field_name)
            )

        try:
            response = execute_query("contractName.keyword")
        except es_exceptions.BadRequestError as exc:
            error_message = str(getattr(exc, "info", exc))
            fallback_signals = (
                "Fielddata is disabled",
                "Field [contractName.keyword] does not exist",
                "No field found for",
                "Unknown field"
            )

            if any(signal in error_message for signal in fallback_signals):
                response = execute_query("contractName")
            else:
                raise

        documents = []
        buckets = (
            response
            .get("aggregations", {})
            .get("documents", {})
            .get("buckets", [])
        )

        file_index = {}
        if UPLOAD_DIR.exists():
            for pdf_path in UPLOAD_DIR.glob("*.pdf"):
                file_index.setdefault(pdf_path.stem, pdf_path)

        for bucket in buckets:
            contract_key = bucket.get("key")
            if not contract_key:
                continue

            doc_count = bucket.get("doc_count", 0)
            file_path = file_index.get(contract_key)

            upload_iso = None
            upload_display = None
            file_size = None
            file_name = None

            if file_path and file_path.exists():
                file_name = file_path.name
                stat_info = file_path.stat()
                upload_dt = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
                upload_iso = upload_dt.isoformat()
                upload_display = upload_dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                file_size = _format_file_size(stat_info.st_size)

            doc_info = {
                "name": contract_key,
                "file_name": file_name or f"{contract_key}.pdf",
                "chunks_count": doc_count,
                "page_count": doc_count,
                "pageCount": doc_count,
                "upload_time": upload_iso,
                "uploadTime": upload_display,
                "status": "indexed",
                "parse_status": "success",
                "parseStatus": "success",
                "data_type": "legacy",
                "dataType": "legacy",
                "file_size": file_size,
                "fileSize": file_size,
                "has_structured_data": False,
                "hasStructuredData": False,
            }

            documents.append(doc_info)

        return {
            "code": 200,
            "message": "获取文档列表成功",
            "total_documents": len(documents),
            "data": documents
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取文档列表失败: {str(e)}",
            "data": []
        }


@app.get("/documents/{document_name}/detail")
async def get_document_detail(document_name: str):
    """
    获取指定文档的详细信息
    """
    try:
        index_name = es_searcher.index_name

        if not es_searcher.es.indices.exists(index=index_name):
            raise HTTPException(status_code=404, detail="索引不存在")

        normalized = Path(document_name).stem or document_name

        query = {
            "query": {
                "term": {
                    "contractName": normalized
                }
            },
            "sort": [
                {"pageId": {"order": "asc"}}
            ]
        }

        try:
            hits = list(helpers.scan(
                es_searcher.es,
                index=index_name,
                query=query,
                size=200,
                preserve_order=True
            ))
        except es_exceptions.NotFoundError:
            raise HTTPException(status_code=404, detail="文档不存在")

        if not hits:
            raise HTTPException(status_code=404, detail="未找到匹配文档")

        pages = []
        total_chars = 0
        for hit in hits:
            source = hit.get("_source", {})
            page_id = source.get("pageId")
            text = source.get("text") or ""
            char_count = len(text)
            total_chars += char_count
            pages.append({
                "pageId": page_id,
                "text": text,
                "charCount": char_count,
            })

        file_path = None
        if UPLOAD_DIR.exists():
            for pdf_path in UPLOAD_DIR.glob("*.pdf"):
                if pdf_path.stem == normalized:
                    file_path = pdf_path
                    break

        upload_iso = None
        upload_display = None
        file_size = None
        contract_display_name = normalized

        if file_path and file_path.exists():
            stat_info = file_path.stat()
            upload_dt = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
            upload_iso = upload_dt.isoformat()
            upload_display = upload_dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            file_size = _format_file_size(stat_info.st_size)
            contract_display_name = file_path.name

        detail = {
            "contract_name": contract_display_name,
            "contractName": contract_display_name,
            "data_type": "legacy",
            "dataType": "legacy",
            "total_pages": len(pages),
            "totalPages": len(pages),
            "total_chars": total_chars,
            "totalChars": total_chars,
            "extractionStatus": "已提取" if pages else "未提取",
            "structured_data": None,
            "structuredData": None,
            "pages": pages,
            "upload_time": upload_iso,
            "uploadTime": upload_display,
            "file_size": file_size,
            "fileSize": file_size,
        }

        if file_path:
            detail["file_name"] = file_path.name
            detail["fileName"] = file_path.name

        return {
            "code": 200,
            "message": "获取文档详情成功",
            "data": detail
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")


# 删除指定文档接口
@app.delete("/documents/{document_name}")
async def delete_document(document_name: str):
    """
    删除指定文档的所有索引
    """
    try:
        result = await run_in_threadpool(es_deleter.delete_by_filename, document_name)
        
        if result['status'] == 'success':
            return {
                "success": True,
                "message": f"文档 {document_name} 已删除",
                "deleted_chunks": result.get('deleted_count', 0),
                "data": result
            }
        else:
            return {
                "success": False,
                "message": f"删除文档 {document_name} 失败",
                "data": result
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"删除文档失败: {str(e)}",
            "data": None
        }


# 清空索引接口
@app.delete("/clear-index")
async def clear_index():
    """
    清空所有文档索引
    """
    try:
        # 删除整个索引
        if es_searcher.es.indices.exists(index=es_searcher.index_name):
            es_searcher.es.indices.delete(index=es_searcher.index_name)
            
            # 重新创建索引（如果需要的话）
            # 这里可以根据需要重新创建索引结构
            
            return {
                "success": True,
                "message": "索引已清空",
                "cleared_index": es_searcher.index_name
            }
        else:
            return {
                "success": True,
                "message": "索引不存在，无需清空",
                "cleared_index": es_searcher.index_name
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"清空索引失败: {str(e)}",
            "data": None
        }


# 健康检查接口
@app.get("/health")
async def health_check():
    try:
        health = es_searcher.es.cluster.health()
        return {
            "code": 200,
            "message": "服务正常",
            "data": {
                "cluster_name": health.get('cluster_name'),
                "status": health.get('status'),
                "number_of_nodes": health.get('number_of_nodes'),
                "active_shards": health.get('active_shards'),
                "index_name": es_searcher.index_name,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")


@app.get("/document/download/{document_name}")
async def download_document(document_name: str):
    """
    下载原始PDF文档
    """
    try:
        # 构建文件路径（统一使用全局上传目录）
        file_path = UPLOAD_DIR / document_name
        
        # 检查文件是否存在
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 返回文件
        return FileResponse(
            path=str(file_path),
            filename=document_name,
            media_type='application/pdf'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


if FRONTEND_INDEX_FILE.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_app(full_path: str):
        target_path = FRONTEND_DIST_PATH / full_path

        if target_path.exists() and target_path.is_file():
            return FileResponse(target_path)

        return FileResponse(FRONTEND_INDEX_FILE)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)