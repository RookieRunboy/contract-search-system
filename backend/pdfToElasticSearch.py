from pdfToText import MultiModalTextExtractor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from elasticsearch import Elasticsearch
from fastapi import HTTPException, UploadFile

from llm_metadata_extractor import MetadataExtractor
from embedding_client import RemoteEmbeddingClient

StatusCallback = Optional[Callable[[str, Dict[str, Any]], None]]



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
        self.extractor: Optional[MultiModalTextExtractor] = None

    def extract_text(self, pdf_bytes, pdf_name=None):
        """
        从PDF字节中提取文本信息

        参数:
        pdf_bytes (bytes): PDF文件的字节内容
        pdf_name (str, optional): PDF文件名，如果未提供则使用默认名称

        返回:
        list: 包含每页文本信息的JSON格式列表
        """
        if self.extractor is None:
            self.extractor = MultiModalTextExtractor()
        return self.extractor.extract_pdf_bytes(pdf_bytes, pdf_name)

class JSONToElasticsearch:
    def __init__(self, es_host: str ="http://localhost:9200", model_name: str ="bge-m3", index_name: str ="contracts_unified"):
        self.embedding_client: Optional[RemoteEmbeddingClient] = None
        try:
            self.es = Elasticsearch(es_host)
            self.embedding_client = RemoteEmbeddingClient(model=model_name)
            self.index_name = index_name
            self.metadata_extractor = MetadataExtractor()
            if not self.es.ping():
                raise ConnectionError("Elasticsearch连接失败")
        except Exception as e:
            print(f"初始化错误:{str(e)}")

    @staticmethod
    def _metadata_has_values(metadata: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(metadata, dict):
            return False

        key_fields = [
            'customer_name',
            'our_entity',
            'customer_category_level1',
            'customer_category_level2',
            'contract_amount',
            'signing_date',
            'project_description',
            'positions',
            'personnel_list',
        ]

        for key in key_fields:
            value = metadata.get(key)
            if value not in (None, "", [], {}):
                return True
        return False

    def load_to_elasticsearch(self, pdf_name: str, pageId: int, text: str, total_pages: int = None, file_size: int = None) -> bool:
        try:
            if not self.embedding_client:
                raise RuntimeError("向量服务未初始化")

            from datetime import datetime
            
            # 生成文本向量
            vector_results = self.embedding_client.embed(text)
            if not vector_results:
                raise ValueError("Remote embedding service returned empty result")
            vector = vector_results[0]

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
                        "customer_name": None,
                        "our_entity": None,
                        "customer_category_level1": None,
                        "customer_category_level2": None,
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

    def extract_and_update_metadata(self, contract_name: str, full_text: str) -> Dict[str, Any]:
        """提取元数据并更新到第一页文档中。"""

        result: Dict[str, Any] = {
            "success": False,
            "metadata": None,
            "metadata_vector_generated": False,
            "has_metadata": False,
            "error": None,
        }

        try:
            metadata_result, metadata_vector = self.metadata_extractor.extract_metadata_from_long_text(full_text)

            if not metadata_result.get('success', False):
                error_msg = metadata_result.get('error', '未知错误')
                result['error'] = error_msg
                print(f"元数据提取失败: {error_msg}")
                return result

            metadata = metadata_result.get('metadata', {}) or {}
            update_data = {
                "document_metadata": {
                    "customer_name": metadata.get('customer_name'),
                    "our_entity": metadata.get('our_entity'),
                    "customer_category_level1": metadata.get('customer_category_level1'),
                    "customer_category_level2": metadata.get('customer_category_level2'),
                    "contract_type": metadata.get('contract_type'),
                    "contract_amount": metadata.get('contract_amount'),
                    "signing_date": metadata.get('signing_date'),
                    "project_description": metadata.get('project_description'),
                    "positions": metadata.get('positions'),
                    "personnel_list": metadata.get('personnel_list'),
                    "extracted_at": metadata.get('extracted_at')
                }
            }

            if metadata_vector is not None:
                update_data["document_metadata"]["metadata_vector"] = metadata_vector.tolist()
                result['metadata_vector_generated'] = True
                print(f"成功生成元数据向量，维度: {metadata_vector.shape}")
            else:
                print("元数据向量生成失败")

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
                message = f"未找到合同 {contract_name} 的第一页文档"
                print(message)
                result['error'] = message
                return result

            doc_id = search_result['hits']['hits'][0]['_id']

            from datetime import datetime
            self.es.update(
                index=self.index_name,
                id=doc_id,
                body={"doc": {**update_data, "updated_at": datetime.now().isoformat()}},
            )

            result['success'] = True
            result['metadata'] = metadata
            result['has_metadata'] = self._metadata_has_values(metadata)
            print(f"成功更新合同 {contract_name} 的元数据")
            return result

        except Exception as e:  # noqa: BLE001
            message = f"提取和更新元数据失败: {str(e)}"
            print(message)
            result['error'] = str(e)
            return result

    def json_to_elasticsearch(
        self,
        contractJson: List[Dict[str, Any]],
        file_size: int = None,
        status_callback: StatusCallback = None,
    ) -> Dict[str, Any]:
        contract_name = None
        total_pages = len(contractJson)

        try:
            if status_callback:
                status_callback(
                    "vectorizing",
                    {
                        "total_pages": total_pages,
                        "processed_pages": 0,
                    },
                )

            for index, page in enumerate(contractJson, start=1):
                contract_name = page['pdf_name']
                self.load_to_elasticsearch(
                    pdf_name=page['pdf_name'],
                    pageId=page['pageId'],
                    text=page['text'],
                    total_pages=total_pages,
                    file_size=file_size,
                )

                if status_callback:
                    status_callback(
                        "vectorizing",
                        {
                            "total_pages": total_pages,
                            "processed_pages": index,
                        },
                    )

            metadata_status = "skipped"
            has_metadata = False
            metadata_error = None

            if contract_name and contractJson:
                full_text = " ".join([page['text'] for page in contractJson])
                print(f"开始提取合同 {contract_name} 的元数据...")

                if status_callback:
                    status_callback("metadata_extracting", {"total_pages": total_pages})

                metadata_result = self.extract_and_update_metadata(contract_name, full_text)

                has_metadata = bool(metadata_result.get('has_metadata'))
                metadata_error = metadata_result.get('error')

                if metadata_result.get('success'):
                    metadata_status = "extracted" if has_metadata else "empty"
                    print(f"合同 {contract_name} 元数据提取和存储完成")
                else:
                    if metadata_error and "跳过" in metadata_error:
                        metadata_status = "skipped"
                    else:
                        metadata_status = "failed"
                    print(f"合同 {contract_name} 元数据提取失败: {metadata_error}")

            result = {
                "contract_name": contract_name,
                "total_pages": total_pages,
                "metadata_status": metadata_status,
                "has_metadata": has_metadata,
                "error": metadata_error,
            }

            if status_callback:
                status_callback(
                    "completed",
                    {
                        "total_pages": total_pages,
                        "page_count": total_pages,
                        "metadata_status": metadata_status,
                        "has_metadata": has_metadata,
                        "error": metadata_error,
                    },
                )

            return result
        except Exception as e:  # noqa: BLE001
            if status_callback:
                status_callback("failed", {"error": str(e)})
            print(f"批量索引失败: {str(e)}")
            raise

class PdfToElasticsearch:
    def __init__(self):
        self.pdfExtractor = PDFTextExtractor()
        self.jsonExtractor = JSONToElasticsearch()
    def process_pdf_bytes(
        self,
        contents: bytes,
        filename: str,
        *,
        status_callback: StatusCallback = None,
    ) -> Dict[str, Any]:
        contract_name = Path(filename).stem

        if status_callback:
            status_callback("parsing", {})

        contract_json = self.pdfExtractor.extract_text(contents, contract_name)

        if not isinstance(contract_json, list) or not contract_json:
            if status_callback:
                status_callback(
                    "failed",
                    {
                        "error": "未识别到任何页面内容",
                    },
                )
            raise RuntimeError("PDF 解析失败：未返回任何页面内容")

        total_pages = len(contract_json)

        error_pages = []
        for page in contract_json:
            text_value = ""
            if isinstance(page, dict):
                text_value = str(page.get("text", "") or "")
            else:
                text_value = str(page)

            if text_value.strip().lower().startswith("error"):
                error_pages.append(page)

        if error_pages:
            first_error = error_pages[0]
            error_text_raw = ""
            if isinstance(first_error, dict):
                error_text_raw = str(first_error.get("text", "") or "")
            else:
                error_text_raw = str(first_error)

            error_message = error_text_raw.split(":", 1)[-1].strip() if ":" in error_text_raw else error_text_raw

            if status_callback:
                status_callback(
                    "failed",
                    {
                        "error": f"页面解析失败: {error_message or '模型未返回结果'}",
                        "total_pages": total_pages,
                        "processed_pages": total_pages - len(error_pages),
                    },
                )

            raise RuntimeError(f"PDF 解析失败：共有 {len(error_pages)} 页解析错误")

        if status_callback:
            status_callback(
                "parsing",
                {
                    "total_pages": total_pages,
                },
            )

        indexing_result = self.jsonExtractor.json_to_elasticsearch(
            contract_json,
            file_size=len(contents),
            status_callback=status_callback,
        )

        return {
            "status": "success",
            "pdf_name": filename,
            "pages": total_pages,
            "contract_name": contract_name,
            "metadata_status": indexing_result.get("metadata_status"),
            "has_metadata": indexing_result.get("has_metadata"),
        }

    def process_file_path(
        self,
        file_path: Path,
        *,
        status_callback: StatusCallback = None,
    ) -> Dict[str, Any]:
        contents = file_path.read_bytes()
        return self.process_pdf_bytes(contents, file_path.name, status_callback=status_callback)

    def start_process(self, file: UploadFile) -> Dict[str, Optional[Union[str, int]]]:
        try:
            allowed_types = [
                'application/pdf',
            ]
            max_file_size = 100 * 1024 * 1024  # 100MB
            if file.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="不支持的文件类型")

            contents = file.file.read()

            if len(contents) > max_file_size:
                raise HTTPException(status_code=400, detail="文件过大")

            upload_dir = Path(__file__).resolve().parent.parent / "uploaded_contracts"
            upload_dir.mkdir(exist_ok=True)

            file_path = upload_dir / file.filename
            with open(file_path, "wb") as f:
                f.write(contents)

            result = self.process_pdf_bytes(contents, file.filename)
            return {"status": "success", "pdf_name": file.filename, "pages": result.get("pages")}

        except Exception as e:  # noqa: BLE001
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
