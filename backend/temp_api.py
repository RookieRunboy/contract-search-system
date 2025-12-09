from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import tempfile
import os
import json

# 新增：导入简单文档处理器用于提取PDF文本并切块
from document_processor import DocumentProcessor

# FastAPI应用
app = FastAPI(title="临时合同检索API")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用启动时加载索引
@app.on_event("startup")
async def startup_event():
    load_index_from_file()

# 索引文件路径
INDEX_FILE_PATH = "index_data.json"

# 简易内存索引：保存上传后的文本块，结构与正式接口尽量一致
# 每个条目形如：{"contract_name": str, "page_id": int, "text": str}
IN_MEMORY_INDEX: List[dict] = []

# 文档处理器（默认参数即可）
processor = DocumentProcessor()

def load_index_from_file():
    """从本地文件加载索引到内存"""
    global IN_MEMORY_INDEX
    try:
        if os.path.exists(INDEX_FILE_PATH):
            with open(INDEX_FILE_PATH, 'r', encoding='utf-8') as f:
                IN_MEMORY_INDEX = json.load(f)
            print(f"已从 {INDEX_FILE_PATH} 加载 {len(IN_MEMORY_INDEX)} 条索引记录")
        else:
            IN_MEMORY_INDEX = []
            print(f"索引文件 {INDEX_FILE_PATH} 不存在，使用空索引")
    except Exception as e:
        print(f"加载索引文件失败: {e}")
        IN_MEMORY_INDEX = []

def save_index_to_file():
    """将内存索引保存到本地文件"""
    try:
        with open(INDEX_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(IN_MEMORY_INDEX, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(IN_MEMORY_INDEX)} 条索引记录到 {INDEX_FILE_PATH}")
    except Exception as e:
        print(f"保存索引文件失败: {e}")
        raise

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "临时合同检索API服务正在运行",
        "version": "1.2.0",
        "endpoints": [
            "/upload - 上传文档（会在内存中建立简单索引并持久化）",
            "/search - 基于内存索引的关键词搜索",
            "/clear-index - 清空索引和删除本地文件",
            "/health - 检查服务状态"
        ],
        "indexed_chunks": len(IN_MEMORY_INDEX),
        "persistence": "enabled"
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档：解析PDF文本并在内存中建立简单索引（不依赖ES）"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")

        # 将上传内容写入临时文件，便于PDF解析
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            content = await file.read()
            tmp.write(content)

        # 使用处理器解析PDF并切块
        try:
            chunks = processor.process_document(temp_path, file.filename)
        finally:
            # 清理临时文件
            try:
                os.remove(temp_path)
            except Exception:
                pass

        # 将切块结果写入内存索引
        added = 0
        filename = file.filename
        for ch in chunks:
            entry = {
                "contract_name": filename,
                "page_id": ch.get("page_number", 1),
                "text": ch.get("content", "")
            }
            IN_MEMORY_INDEX.append(entry)
            added += 1

        # 保存索引到本地文件
        save_index_to_file()

        return {
            "success": True,
            "message": f"文档 {filename} 上传并已建立内存索引",
            "filename": filename,
            "file_size": len(content),
            "chunks_count": len(chunks),
            "indexed": added,
            "total_index_size": len(IN_MEMORY_INDEX)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.get("/search")
async def search_documents(
        query: str = Query(..., description="搜索关键词"),
        top_k: Optional[int] = Query(default=5, description="返回结果数量")
):
    """基于内存索引的简单关键词搜索（子串匹配 + 频次评分）"""
    try:
        if not query or not IN_MEMORY_INDEX:
            return {
                "code": 200,
                "message": "搜索成功（内存索引）",
                "query": query,
                "total_results": 0,
                "data": []
            }

        q = query.lower()
        results: List[dict] = []
        for item in IN_MEMORY_INDEX:
            text = item.get("text", "")
            t = text.lower()
            if q in t:
                # 简单打分：出现次数 + 文本长度惩罚（避免超长文本优势）
                count = t.count(q)
                score = count / max(1.0, len(t) / 1000.0)
                results.append({
                    "score": float(score),
                    "contract_name": item.get("contract_name", "未知文档"),
                    "page_id": int(item.get("page_id", 1)),
                    "text": text
                })

        # 排序与截断
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[: max(1, int(top_k or 5))]

        return {
            "code": 200,
            "message": "搜索成功（内存索引）",
            "query": query,
            "total_results": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索异常: {str(e)}")

@app.delete("/clear-index")
async def clear_index():
    """清空索引和删除本地文件"""
    global IN_MEMORY_INDEX
    try:
        # 清空内存索引
        old_count = len(IN_MEMORY_INDEX)
        IN_MEMORY_INDEX = []
        
        # 删除本地索引文件
        if os.path.exists(INDEX_FILE_PATH):
            os.remove(INDEX_FILE_PATH)
            file_deleted = True
        else:
            file_deleted = False
        
        return {
            "success": True,
            "message": "索引已清空",
            "cleared_chunks": old_count,
            "file_deleted": file_deleted,
            "current_index_size": len(IN_MEMORY_INDEX)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空索引失败: {str(e)}")

@app.get("/documents")
async def get_uploaded_documents():
    """获取已上传的文档列表"""
    try:
        # 从内存索引中提取唯一的文档信息
        documents = {}
        for item in IN_MEMORY_INDEX:
            contract_name = item.get("contract_name", "未知文档")
            if contract_name not in documents:
                documents[contract_name] = {
                    "name": contract_name,
                    "chunks_count": 0,
                    "upload_time": None,  # 暂时无法获取上传时间
                    "status": "indexed"
                }
            documents[contract_name]["chunks_count"] += 1
        
        document_list = list(documents.values())
        
        return {
            "code": 200,
            "message": "获取文档列表成功",
            "total_documents": len(document_list),
            "data": document_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@app.delete("/documents/{document_name}")
async def delete_document(document_name: str):
    """删除指定文档的所有索引"""
    global IN_MEMORY_INDEX
    try:
        # 删除指定文档的所有索引条目
        original_count = len(IN_MEMORY_INDEX)
        IN_MEMORY_INDEX = [item for item in IN_MEMORY_INDEX if item.get("contract_name") != document_name]
        deleted_count = original_count - len(IN_MEMORY_INDEX)
        
        # 保存更新后的索引
        save_index_to_file()
        
        return {
            "success": True,
            "message": f"文档 {document_name} 已删除",
            "deleted_chunks": deleted_count,
            "remaining_chunks": len(IN_MEMORY_INDEX)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "code": 200,
        "message": "临时服务正常",
        "status": "running",
        "indexed_chunks": len(IN_MEMORY_INDEX)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)