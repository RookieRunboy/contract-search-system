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
    def __init__(self, es_host: str ="http://localhost:9200", model_name: str ="BAAI/bge-base-zh", index_name: str ="contracts_vector"):
        try:
            self.es = Elasticsearch(es_host)
            self.model = SentenceTransformer(model_name)
            self.index_name = index_name
            if not self.es.ping():
                raise ConnectionError("Elasticsearch连接失败")
        except Exception as e:
            print(f"初始化错误:{str(e)}")

    def load_to_elasticsearch(self, pdf_name: str, pageId: int, text: str) -> bool:
        try:
            # 生成文本向量
            vector = self.model.encode(text).tolist()

            # 构建文档
            document = {
                "contractName": pdf_name,
                "pageId": pageId,
                "text": text,
                "text_vector": vector
            }

            self.es.index(index=self.index_name, body=document)

            return True

        except Exception as e:
            print(f"{str(e)}")
            return False

    def json_to_elasticsearch(self, contractJson: List[Dict[str, Any]]) -> bool:
        try:
            for page in contractJson:
                self.load_to_elasticsearch(
                    pdf_name=page['pdf_name'],
                    pageId=page['pageId'],
                    text=page['text']
                )
            return True
        except Exception as e:
            print(f"{str(e)}")
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
            self.jsonExtractor.json_to_elasticsearch(result)
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