from simple_pdf_extractor_backup import SimplePDFExtractor
from pathlib import Path
import json
import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
import shutil
from llm_metadata_extractor import MetadataExtractor
import numpy as np



class PDFTextExtractor:
    """
    PDF文本提取器
    用于从PDF字节中提取文本信息
    """

    def __init__(self, lang_list=["ch"], table_enable=True, formula_enable=False):
        """
        初始化PDF文本提取器

        参数:
        lang_list (list): 语言列表，默认为中文
        table_enable (bool): 是否启用表格提取，默认为True
        formula_enable (bool): 是否启用公式提取，默认为False
        """
        self.extractor = SimplePDFExtractor()

    def extract_text(self, pdf_bytes, pdf_name=None):
        """
        从PDF字节中提取文本信息

        参数:
        pdf_bytes (bytes): PDF文件的字节内容
        pdf_name (str, optional): PDF文件名，如果未提供则使用默认名称

        返回:
        list: 包含每页文本信息的JSON格式列表
        """
        return self.extractor.extract_text(pdf_bytes, pdf_name)

class JSONToElasticsearch:
    def __init__(self, es_host: str ="http://localhost:9200", model_name: str ="BAAI/bge-base-zh", index_name: str ="contracts_unified"):
        try:
            self.es = Elasticsearch(es_host)
            self.model = SentenceTransformer(model_name)
            self.index_name = index_name
            self.metadata_extractor = MetadataExtractor()
            if not self.es.ping():
                raise ConnectionError("Elasticsearch连接失败")
        except Exception as e:
            print(f"初始化错误:{str(e)}")

    def load_to_elasticsearch(self, pdf_name: str, pageId: int, text: str, total_pages: int = None, file_size: int = None) -> bool:
        try:
            from datetime import datetime
            
            # 生成文本向量
            vector = self.model.encode(text).tolist()

            # 构建基础文档
            document = {
                "contractName": pdf_name,
                "pageId": pageId,
                "text": text,
                "text_vector": vector,
                "doc_type": "page_content",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # 如果是第一页，添加文档级别的元数据占位字段
            if pageId == 1:
                document.update({
                    "document_metadata": {
                        "party_a": None,
                        "party_b": None,
                        "contract_type": None,
                        "contract_amount": None,
                        "signing_date": None,
                        "project_description": None,
                        "positions": None,
                        "personnel_list": None,
                        "extracted_at": None
                    },
                    "total_pages": total_pages,
                    "file_size": file_size
                })

            self.es.index(index=self.index_name, body=document)
            return True

        except Exception as e:
            print(f"索引文档失败: {str(e)}")
            return False

    def extract_and_update_metadata(self, contract_name: str, full_text: str) -> bool:
        """
        提取元数据并更新到第一页文档中
        
        Args:
            contract_name: 合同名称
            full_text: 完整合同文本
        
        Returns:
            bool: 是否成功更新元数据
        """
        try:
            # 提取元数据和向量
            metadata_result, metadata_vector = self.metadata_extractor.extract_metadata(full_text)
            
            if not metadata_result.get('success', False):
                print(f"元数据提取失败: {metadata_result.get('error', '未知错误')}")
                return False
            
            metadata = metadata_result.get('metadata', {})
            
            # 准备更新的元数据
            update_data = {
                "document_metadata": {
                    "party_a": metadata.get('party_a'),
                    "party_b": metadata.get('party_b'),
                    "contract_type": metadata.get('contract_type'),
                    "contract_amount": metadata.get('contract_amount'),
                    "signing_date": metadata.get('signing_date'),
                    "project_description": metadata.get('project_description'),
                    "positions": metadata.get('positions'),
                    "personnel_list": metadata.get('personnel_list'),
                    "extracted_at": metadata.get('extracted_at')
                }
            }
            
            # 如果成功生成了元数据向量，添加到更新数据中
            if metadata_vector is not None:
                update_data["document_metadata"]["metadata_vector"] = metadata_vector.tolist()
                print(f"成功生成元数据向量，维度: {metadata_vector.shape}")
            else:
                print("元数据向量生成失败")
            
            # 查询第一页文档
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
            
            search_result = self.es.search(index=self.index_name, body=query)
            
            if search_result['hits']['total']['value'] == 0:
                print(f"未找到合同 {contract_name} 的第一页文档")
                return False
            
            # 更新第一页文档的元数据
            doc_id = search_result['hits']['hits'][0]['_id']
            
            from datetime import datetime
            self.es.update(
                index=self.index_name,
                id=doc_id,
                body={"doc": {**update_data, "updated_at": datetime.now().isoformat()}}
            )
            
            print(f"成功更新合同 {contract_name} 的元数据")
            return True
            
        except Exception as e:
            print(f"提取和更新元数据失败: {str(e)}")
            return False

    def json_to_elasticsearch(self, contractJson: List[Dict[str, Any]], file_size: int = None) -> bool:
        try:
            total_pages = len(contractJson)
            contract_name = None
            
            # 首先索引所有页面
            for page in contractJson:
                contract_name = page['pdf_name']  # 记录合同名称
                self.load_to_elasticsearch(
                    pdf_name=page['pdf_name'],
                    pageId=page['pageId'],
                    text=page['text'],
                    total_pages=total_pages,
                    file_size=file_size
                )
            
            # 合并所有页面文本用于元数据提取
            if contract_name and contractJson:
                full_text = " ".join([page['text'] for page in contractJson])
                print(f"开始提取合同 {contract_name} 的元数据...")
                
                # 提取并更新元数据
                metadata_success = self.extract_and_update_metadata(contract_name, full_text)
                if metadata_success:
                    print(f"合同 {contract_name} 元数据提取和存储完成")
                else:
                    print(f"合同 {contract_name} 元数据提取失败，但文档已成功索引")
            
            return True
        except Exception as e:
            print(f"批量索引失败: {str(e)}")
            return False

class PdfToElasticsearch:
    def __init__(self):
        self.pdfExtractor = PDFTextExtractor()
        self.jsonExtractor = JSONToElasticsearch()
    def start_process(self, file: UploadFile) -> dict[str, str | None | int]:
        try:
            allowed_types = [
                'application/pdf',
            ]
            max_file_size = 100 * 1024 * 1024  # 100MB
            if file.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="不支持的文件类型")

            # 读取文件内容
            contents = file.file.read()

            # 文件大小检查
            if len(contents) > max_file_size:
                raise HTTPException(status_code=400, detail="文件过大")

            # 创建上传文件存储目录（统一到项目根目录）
            upload_dir = Path(__file__).resolve().parent.parent / "uploaded_contracts"
            upload_dir.mkdir(exist_ok=True)
            
            # 保存原始PDF文件
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as f:
                f.write(contents)

            result = self.pdfExtractor.extract_text(contents, Path(file.filename).stem)
            self.jsonExtractor.json_to_elasticsearch(result, file_size=len(contents))
            return {"status": "success", "pdf_name": file.filename, "pages": len(result)}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 创建提取器实例
    pdfExtractor = PDFTextExtractor()
    jsonExtractor = JSONToElasticsearch()

    # PDF文件路径
    pdf_path = Path("2.pdf")

    # 读取PDF字节
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 提取文本，使用文件名作为标识
    result = pdfExtractor.extract_text(pdf_bytes, pdf_path.stem)
    if(jsonExtractor.json_to_elasticsearch(result)):
        print("成功")

    # # 打印结果
    # print(json.dumps(result, ensure_ascii=False, indent=2))
    #
    # # 可选：保存为JSON文件
    # with open("content_list.json", "w", encoding="utf-8") as f:
    #     json.dump(result, f, ensure_ascii=False, indent=2)
