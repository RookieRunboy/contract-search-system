from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Optional, Union
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from pathlib import Path
import os

from pdfToElasticSearch import PdfToElasticsearch
from elasticSearchDelete import ElasticsearchDocumentDeleter
from elasticSearchSearch import ElasticsearchVectorSearch
from elasticSearchOutput import get_document_by_filename
from llm_metadata_extractor import MetadataExtractor
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
doc_getter = get_document_by_filename()
metadata_extractor = MetadataExtractor()


@app.get("/document/list")
async def get_document_list():
    """
    获取已上传的文档列表
    """
    try:
        # 首先检查Elasticsearch连接
        if not es_searcher.es.ping():
            print("ERROR: Elasticsearch连接失败")
            return {
                "code": 500,
                "message": "Elasticsearch连接失败",
                "data": []
            }
        
        # 检查索引是否存在
        index_name = "contracts_unified"
        if not es_searcher.es.indices.exists(index=index_name):
            print(f"ERROR: 索引 {index_name} 不存在")
            return {
                "code": 200,
                "message": "索引不存在，返回空列表",
                "data": []
            }
        
        # 使用聚合查询获取所有文档的基本信息
        agg_query = {
            "size": 0,
            "aggs": {
                "documents": {
                    "terms": {
                        "field": "contractName",
                        "size": 1000
                    },
                    "aggs": {
                        "page_count": {
                            "cardinality": {
                                "field": "pageId"
                            }
                        },
                        "first_page": {
                            "filter": {
                                "term": {"pageId": 1}
                            },
                            "aggs": {
                                "first_doc": {
                                    "top_hits": {
                                        "size": 1,
                                        "sort": [
                                            {"updated_at": {"order": "desc"}}
                                        ],
                                        "_source": {
                                            "includes": [
                                                "document_metadata",
                                                "updated_at"
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        print(f"DEBUG: 执行聚合查询: {agg_query}")
        
        # 查询统一索引
        response = es_searcher.es.search(
            index=index_name,
            body=agg_query
        )
        
        print(f"DEBUG: Elasticsearch响应: {response}")
        
        documents = []
        buckets = response.get('aggregations', {}).get('documents', {}).get('buckets', [])
        
        print(f"DEBUG: 找到 {len(buckets)} 个文档桶")
        
        for bucket in buckets:
            try:
                contract_name = bucket['key']
                page_count = bucket['page_count']['value']
                
                # 从文件系统获取上传时间
                upload_time = None
                try:
                    # 查找对应的PDF文件
                    for pdf_path in UPLOAD_DIR.glob("*.pdf"):
                        if pdf_path.stem == contract_name or pdf_path.name == contract_name:
                            stat_info = pdf_path.stat()
                            from datetime import datetime, timezone
                            upload_dt = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
                            upload_time = upload_dt.isoformat()
                            break
                except Exception as file_error:
                    print(f"WARNING: 无法获取文档 {contract_name} 的文件时间: {str(file_error)}")
                
                # 如果无法从文件系统获取时间，使用当前时间
                if not upload_time:
                    from datetime import datetime
                    upload_time = datetime.now().isoformat()
                    print(f"WARNING: 文档 {contract_name} 使用当前时间作为上传时间")
                
                # 检查元数据状态
                first_page_agg = bucket.get('first_page', {})
                first_doc_hits = first_page_agg.get('first_doc', {}).get('hits', {}).get('hits', [])
                raw_metadata = None
                if first_doc_hits:
                    raw_source = first_doc_hits[0].get('_source', {}) or {}
                    raw_metadata = raw_source.get('document_metadata')

                # 判断元数据是否“已提取”：关键字段是否至少有一个非空
                def _is_non_empty(v):
                    return v is not None and v != "" and v != [] and v != {}

                has_metadata = False
                if isinstance(raw_metadata, dict) and raw_metadata:
                    key_fields = [
                        'party_a', 'party_b', 'contract_type', 'contract_amount',
                        'project_description', 'positions', 'personnel_list'
                    ]
                    has_metadata = any(_is_non_empty(raw_metadata.get(k)) for k in key_fields)

                metadata_status = 'extracted' if has_metadata else 'not_extracted'
                
                documents.append({
                    "contract_name": contract_name,
                    "page_count": page_count,
                    "upload_time": upload_time,
                    "has_metadata": has_metadata,
                    "metadata_status": metadata_status
                })
                
            except Exception as bucket_error:
                print(f"ERROR: 处理文档桶时出错: {str(bucket_error)}, 桶数据: {bucket}")
                continue
        
        # 按上传时间倒序排列
        try:
            documents.sort(key=lambda x: x['upload_time'], reverse=True)
        except Exception as sort_error:
            print(f"WARNING: 排序失败: {str(sort_error)}, 使用原始顺序")
        
        print(f"DEBUG: 成功处理 {len(documents)} 个文档")

        return {
            "code": 200,
            "message": "获取文档列表成功",
            "data": documents
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR: 获取文档列表失败: {str(e)}")
        print(f"ERROR: 详细错误信息: {error_details}")
        return {
            "code": 500,
            "message": f"获取文档列表失败: {str(e)}",
            "data": []
        }

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
            "/document/extract-metadata",
            "/document/save-metadata",
            "/document/download/{document_name}"
        ],
    }


@app.post("/document/add")
async def upload_document(
    files: List[UploadFile] = File(..., description="上传的PDF合同文件，支持一次选择多个")
):
    """
    上传PDF文档并索引到Elasticsearch
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")

    success_results: List[Dict[str, Union[str, int, None]]] = []
    failed_results: List[Dict[str, Union[str, int]]] = []

    for upload in files:
        filename = upload.filename or "unknown"

        try:
            # 确保游标位于文件开头
            try:
                upload.file.seek(0)
            except Exception:
                pass

            result = await run_in_threadpool(pdf_to_es.start_process, upload)
            success_results.append(result)
        except HTTPException as e:
            failed_results.append({
                "status": "failed",
                "pdf_name": filename,
                "error": e.detail,
                "code": e.status_code,
            })
        except Exception as e:
            failed_results.append({
                "status": "failed",
                "pdf_name": filename,
                "error": str(e),
                "code": 500,
            })
        finally:
            # 关闭临时文件，释放资源
            try:
                await upload.close()
            except Exception:
                pass

    if not success_results and failed_results:
        # 若全部失败，则直接抛出异常，便于前端统一处理
        first_error = failed_results[0]
        raise HTTPException(
            status_code=first_error.get("code", 500),
            detail=first_error.get("error", "文档上传失败"),
        )

    message_parts = []
    if success_results:
        message_parts.append(f"成功上传 {len(success_results)} 个文件")
    if failed_results:
        message_parts.append(f"失败 {len(failed_results)} 个文件")

    return {
        "code": 200,
        "message": "，".join(message_parts) if message_parts else "文档上传完成",
        "data": {
            "success": success_results,
            "failed": failed_results,
        }
    }


# 兼容别名：POST /upload -> /document/add
@app.post("/upload")
async def upload_alias(
    files: List[UploadFile] = File(..., description="上传的PDF合同文件，支持一次选择多个")
):
    return await upload_document(files)


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
        # 兼容旧版本的query参数
        query: Optional[str] = Query(default=None, description="搜索关键词（兼容参数）"),
        # 新版本的分离参数
        query_content: Optional[str] = Query(default=None, description="内容搜索关键词"),
        query_metadata: Optional[str] = Query(default=None, description="元数据搜索关键词"),
        search_mode: Optional[str] = Query(default="content", description="搜索模式：content/metadata/hybrid"),
        # 筛选参数
        amount_min: Optional[float] = Query(default=None, description="合同金额最小值"),
        amount_max: Optional[float] = Query(default=None, description="合同金额最大值"),
        date_start: Optional[str] = Query(default=None, description="合同签订开始日期 (YYYY-MM-DD)"),
        date_end: Optional[str] = Query(default=None, description="合同签订结束日期 (YYYY-MM-DD)"),
        # 其他参数保持不变
        top_k: Optional[int] = Query(default=3, description="返回结果数量"),
        text_standard: Optional[int] = Query(default=3, description="标准文本权重"),
        text_ngram: Optional[int] = Query(default=1, description="N-gram文本权重"),
        vector_weight: Optional[float] = Query(default=5.0, description="向量权重"),
        metadata_weight: Optional[float] = Query(default=3.0, description="元数据权重"),
        fuzziness: Optional[str] = Query(default="AUTO", description="模糊匹配级别")
):
    """
    文档搜索接口（支持混合检索）
    """
    try:
        # 处理兼容性：如果使用旧版query参数，则作为内容搜索
        if query and not query_content and not query_metadata:
            query_content = query
            search_mode = "content"
        
        # 参数校验
        if search_mode not in ("content", "metadata", "hybrid"):
            raise HTTPException(status_code=400, detail="search_mode 必须为 content/metadata/hybrid")
        
        # 根据搜索模式验证必要参数
        if search_mode == "content" and not query_content:
            raise HTTPException(status_code=400, detail="内容搜索模式需要 query_content 参数")
        elif search_mode == "metadata" and not query_metadata:
            raise HTTPException(status_code=400, detail="元数据搜索模式需要 query_metadata 参数")
        elif search_mode == "hybrid" and not query_content and not query_metadata:
            raise HTTPException(status_code=400, detail="混合搜索模式需要至少一个查询参数")

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
            mw_val = float(metadata_weight) if metadata_weight is not None else 3.0
        except Exception:
            raise HTTPException(status_code=400, detail="权重参数必须为数字")
        if vw_val < 0 or vw_val > 10 or mw_val < 0 or mw_val > 10:
            raise HTTPException(status_code=400, detail="权重取值范围为 0-10")

        if fuzziness not in ("AUTO", "0", "1", "2"):
            raise HTTPException(status_code=400, detail="fuzziness 仅支持 AUTO/0/1/2")

        # 验证筛选参数
        if amount_min is not None and amount_min < 0:
            raise HTTPException(status_code=400, detail="amount_min 必须为非负数")
        if amount_max is not None and amount_max < 0:
            raise HTTPException(status_code=400, detail="amount_max 必须为非负数")
        if amount_min is not None and amount_max is not None and amount_min > amount_max:
            raise HTTPException(status_code=400, detail="amount_min 不能大于 amount_max")
        
        # 验证日期格式
        from datetime import datetime
        if date_start is not None:
            try:
                datetime.strptime(date_start, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="date_start 格式必须为 YYYY-MM-DD")
        if date_end is not None:
            try:
                datetime.strptime(date_end, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="date_end 格式必须为 YYYY-MM-DD")
        if date_start is not None and date_end is not None and date_start > date_end:
            raise HTTPException(status_code=400, detail="date_start 不能晚于 date_end")

        # 调用新的搜索接口
        results = await run_in_threadpool(
            es_searcher.search,
            query_content or "",
            query_metadata=query_metadata or "",
            search_mode=search_mode,
            top_k=top_k_val,
            text_standard=ts_val,
            text_ngram=tn_val,
            vector_weight=vw_val,
            metadata_weight=mw_val,
            fuzziness=fuzziness,
            amount_min=amount_min,
            amount_max=amount_max,
            date_start=date_start,
            date_end=date_end
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
        # 兼容旧版本的query参数
        query: Optional[str] = Query(default=None, description="搜索关键词（兼容参数）"),
        # 新版本的分离参数
        query_content: Optional[str] = Query(default=None, description="内容搜索关键词"),
        query_metadata: Optional[str] = Query(default=None, description="元数据搜索关键词"),
        search_mode: Optional[str] = Query(default="content", description="搜索模式：content/metadata/hybrid"),
        # 筛选参数
        amount_min: Optional[float] = Query(default=None, description="合同金额最小值"),
        amount_max: Optional[float] = Query(default=None, description="合同金额最大值"),
        date_start: Optional[str] = Query(default=None, description="合同签订开始日期 (YYYY-MM-DD)"),
        date_end: Optional[str] = Query(default=None, description="合同签订结束日期 (YYYY-MM-DD)"),
        # 其他参数保持不变
        top_k: Optional[int] = Query(default=3, description="返回结果数量"),
        text_standard: Optional[int] = Query(default=3, description="标准文本权重"),
        text_ngram: Optional[int] = Query(default=1, description="N-gram文本权重"),
        vector_weight: Optional[float] = Query(default=5.0, description="向量权重"),
        metadata_weight: Optional[float] = Query(default=3.0, description="元数据权重"),
        fuzziness: Optional[str] = Query(default="AUTO", description="模糊匹配级别")
):
    return await search_documents(
        query=query,
        query_content=query_content,
        query_metadata=query_metadata,
        search_mode=search_mode,
        amount_min=amount_min,
        amount_max=amount_max,
        date_start=date_start,
        date_end=date_end,
        top_k=top_k,
        text_standard=text_standard,
        text_ngram=text_ngram,
        vector_weight=vector_weight,
        metadata_weight=metadata_weight,
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


# 兼容别名：GET /documents -> /document/list
@app.get("/documents")
async def get_uploaded_documents():
    """
    获取已上传的文档列表（兼容接口）
    """
    return await get_document_list()


@app.get("/documents/{document_name}/detail")
async def get_document_detail(document_name: str):
    """
    获取指定文档的详细信息
    """
    try:
        index_name = es_searcher.index_name

        if not es_searcher.es.indices.exists(index=index_name):
            raise HTTPException(status_code=404, detail="索引不存在")

        name_only = Path(document_name).name
        normalized = name_only[:-4] if name_only.lower().endswith('.pdf') else name_only

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
        document_metadata = None
        metadata_status = "not_extracted"
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

            if document_metadata is None:
                raw_metadata = source.get("document_metadata")
                if isinstance(raw_metadata, dict) and raw_metadata:
                    document_metadata = raw_metadata

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

        # 判断是否“已提取”：关键字段至少有一个非空
        def _is_non_empty(v):
            return v is not None and v != "" and v != [] and v != {}

        has_metadata_flag = False
        if isinstance(document_metadata, dict) and document_metadata:
            key_fields = [
                'party_a', 'party_b', 'contract_type', 'contract_amount',
                'project_description', 'positions', 'personnel_list'
            ]
            has_metadata_flag = any(_is_non_empty(document_metadata.get(k)) for k in key_fields)

        metadata_status = 'extracted' if has_metadata_flag else 'not_extracted'

        detail = {
            "contract_name": contract_display_name,
            "contractName": contract_display_name,
            "data_type": "legacy",
            "dataType": "legacy",
            "total_pages": len(pages),
            "totalPages": len(pages),
            "total_chars": total_chars,
            "totalChars": total_chars,
            "extractionStatus": "已提取" if has_metadata_flag else "未提取",
            "structured_data": document_metadata,
            "structuredData": document_metadata,
            "document_metadata": document_metadata,
            "metadata_status": metadata_status,
            "metadataStatus": metadata_status,
            "has_metadata": has_metadata_flag,
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


@app.get("/debug/documents")
async def debug_documents():
    """
    调试用：获取所有文档的详细信息，包括text和text_vector字段
    """
    try:
        # 检查Elasticsearch连接
        if not es_searcher.es.ping():
            return {
                "code": 500,
                "message": "Elasticsearch连接失败",
                "data": []
            }
        
        # 检查索引是否存在
        index_name = "contracts_unified"
        if not es_searcher.es.indices.exists(index=index_name):
            return {
                "code": 200,
                "message": "索引不存在",
                "data": []
            }
        
        # 查询所有文档，包括text和text_vector字段
        query = {
            "query": {"match_all": {}},
            "_source": ["contractName", "pageId", "text", "text_vector"],
            "size": 50  # 限制返回数量
        }
        
        response = es_searcher.es.search(
            index=index_name,
            body=query
        )
        
        documents = []
        hits = response.get('hits', {}).get('hits', [])
        
        for hit in hits:
            source = hit.get('_source', {})
            doc_info = {
                "contractName": source.get('contractName'),
                "pageId": source.get('pageId'),
                "has_text": bool(source.get('text')),
                "text_length": len(source.get('text', '')),
                "has_text_vector": bool(source.get('text_vector')),
                "text_vector_length": len(source.get('text_vector', [])),
                "text_preview": source.get('text', '')[:200] + '...' if source.get('text') else None
            }
            documents.append(doc_info)
        
        return {
            "code": 200,
            "message": f"找到 {len(documents)} 个文档",
            "data": documents
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR: 调试查询失败: {str(e)}")
        print(f"ERROR: 详细错误信息: {error_details}")
        return {
            "code": 500,
            "message": f"调试查询失败: {str(e)}",
            "data": []
        }


@app.post("/document/extract-metadata")
async def extract_metadata(filename: str = Query(..., description="要提取元数据的文件名")):
    """
    从文档中提取元数据
    """
    try:
        # 从Elasticsearch获取文档原始文本
        document_text = await run_in_threadpool(doc_getter.get_document_text, filename)
        
        if not document_text:
            raise HTTPException(status_code=404, detail="文档不存在或无法获取文档内容")
        
        # 调用LLM进行元数据提取
        result, metadata_vector = await run_in_threadpool(
            metadata_extractor.extract_metadata, 
            document_text
        )
        
        if result['success']:
            # 确保元数据中包含合同名称（使用文件名）
            metadata = result['metadata'].copy()
            metadata['contract_name'] = filename
            
            return {
                "code": 200,
                "message": "元数据提取成功",
                "data": {
                    "filename": filename,
                    "metadata": metadata,
                    "document_length": len(document_text),
                    "raw_response": result.get('raw_response')
                }
            }
        else:
            return {
                "code": 500,
                "message": f"元数据提取失败: {result['error']}",
                "data": {
                    "filename": filename,
                    "error": result['error'],
                    "document_length": len(document_text)
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "code": 500,
            "message": f"元数据提取失败: {str(e)}",
            "data": None
        }


@app.post("/document/save-metadata")
async def save_metadata(request: dict):
    """
    保存文档元数据到统一索引的document_metadata字段
    """
    try:
        filename = request.get('filename')
        metadata = request.get('metadata')
        
        if not filename or not metadata:
            raise HTTPException(status_code=400, detail="缺少必要参数：filename 或 metadata")
        
        # 获取文件名（去除扩展名）
        name_only = Path(filename).name
        contract_name = name_only[:-4] if name_only.lower().endswith('.pdf') else name_only
        
        # 查找第一页文档（pageId=1）
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"contractName": contract_name}},
                        {"term": {"pageId": 1}}
                    ]
                }
            }
        }
        
        # 使用统一索引
        index_name = "contracts_unified"
        
        # 搜索第一页文档
        response = es_searcher.es.search(
            index=index_name,
            body=query,
            size=1
        )
        
        hits = response.get('hits', {}).get('hits', [])
        if not hits:
            raise HTTPException(status_code=404, detail="未找到对应的文档第一页")
        
        doc_id = hits[0]['_id']
        
        # 准备元数据更新
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata_update = {
            "party_a": metadata.get('party_a'),
            "party_b": metadata.get('party_b'),
            "contract_type": metadata.get('contract_type'),
            "contract_amount": metadata.get('contract_amount'),
            "signing_date": metadata.get('signing_date'),
            "project_description": metadata.get('project_description'),
            "positions": metadata.get('positions'),
            "personnel_list": metadata.get('personnel_list'),
            "extracted_at": now_iso
        }
        
        # 更新文档的document_metadata字段
        update_body = {
            "doc": {
                "document_metadata": metadata_update,
                "updated_at": now_iso
            }
        }

        # 执行更新
        es_searcher.es.update(
            index=index_name,
            id=doc_id,
            body=update_body
        )

        # 立即刷新索引，确保后续查询可以拿到最新的提取状态
        es_searcher.es.indices.refresh(index=index_name)
        
        return {
            "code": 200,
            "message": "元数据保存成功",
            "data": {
                "filename": filename,
                "contract_name": contract_name,
                "metadata": metadata_update,
                "saved_at": metadata_update["extracted_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "code": 500,
            "message": f"元数据保存失败: {str(e)}",
            "data": None
        }


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


# 前端静态文件服务（可选）
# 如果前端dist文件存在，则提供静态文件服务
if FRONTEND_INDEX_FILE.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_app(full_path: str):
        target_path = FRONTEND_DIST_PATH / full_path

        if target_path.exists() and target_path.is_file():
            return FileResponse(target_path)

        return FileResponse(FRONTEND_INDEX_FILE)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
