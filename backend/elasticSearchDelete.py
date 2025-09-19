from elasticsearch import Elasticsearch
from pathlib import Path

class ElasticsearchDocumentDeleter:
    def __init__(
        self,
        es_host: str = "http://localhost:9200",
        index_name: str = "contracts_vector"
    ):
        """
        初始化Elasticsearch文档删除器

        :param es_host: Elasticsearch服务器地址
        :param index_name: 索引名称
        """
        try:
            self.es = Elasticsearch(es_host)
            self.index_name = index_name
            # 统一上传目录到项目根的 uploaded_contracts
            self.upload_dir = Path(__file__).resolve().parent.parent / "uploaded_contracts"

            # 检查连接
            if not self.es.ping():
                raise ConnectionError("Elasticsearch连接失败")
        except Exception as e:
            print(f"初始化错误: {str(e)}")
            raise

    def _remove_local_files(self, normalized: str) -> dict:
        """删除本地上传目录中匹配的 PDF 文件"""
        removed_files = []
        removal_errors = []

        if not self.upload_dir.exists():
            return {
                "removed_files": removed_files,
                "errors": removal_errors,
                "upload_dir_missing": True
            }

        for pdf_path in self.upload_dir.glob("*.pdf"):
            if pdf_path.stem != normalized:
                continue

            try:
                pdf_path.unlink()
                removed_files.append(pdf_path.name)
            except Exception as err:
                removal_errors.append({
                    "file": pdf_path.name,
                    "error": str(err)
                })

        return {
            "removed_files": removed_files,
            "errors": removal_errors,
            "upload_dir_missing": False
        }

    def _normalize_filename(self, filename: str) -> str:
        """
        规范化文件名：
        - 支持传入 example 或 example.pdf 或包含路径的 /path/example.pdf
        - 实际索引中的 contractName 存的是文件名的"无扩展名"部分
        """
        try:
            name = Path(filename).name  # 去掉路径
            stem = Path(name).stem      # 去掉扩展名
            return stem
        except Exception:
            return filename

    def delete_by_filename(self, filename: str) -> dict:
        """
        根据文件名删除所有相关文档

        :param filename: 要删除的文件名（可带或不带 .pdf 扩展名）
        :return: 删除操作的结果
        """
        try:
            normalized = self._normalize_filename(filename)

            # 构建查询体，匹配指定文件名（规范化后）的所有文档
            query = {
                "query": {
                    "term": {
                        "contractName": normalized
                    }
                }
            }

            # 执行删除操作
            result = self.es.delete_by_query(
                index=self.index_name,
                body=query
            )

            cleanup_result = self._remove_local_files(normalized)

            return {
                "status": "success",
                "deleted_count": result.get('deleted', 0),
                "filename": filename,
                "normalized_filename": normalized,
                **cleanup_result
            }

        except Exception as e:
            print(f"删除文档时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "filename": filename
            }

    def delete_by_page_id(self, filename: str, page_id: int) -> dict:
        """
        根据文件名和页码删除特定文档

        :param filename: 文件名（可带或不带 .pdf 扩展名）
        :param page_id: 页码
        :return: 删除操作的结果
        """
        try:
            normalized = self._normalize_filename(filename)

            # 构建查询体，匹配指定文件名和页码的文档
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"contractName": normalized}},
                            {"term": {"pageId": page_id}}
                        ]
                    }
                }
            }

            # 执行删除操作
            result = self.es.delete_by_query(
                index=self.index_name,
                body=query
            )

            return {
                "status": "success",
                "deleted_count": result.get('deleted', 0),
                "filename": filename,
                "normalized_filename": normalized,
                "page_id": page_id
            }

        except Exception as e:
            print(f"删除文档时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "filename": filename,
                "page_id": page_id
            }

if __name__ == "__main__":
    try:
        # 创建删除器实例
        deleter = ElasticsearchDocumentDeleter()

        # 按文件名删除（支持 example 或 example.pdf 或 /path/example.pdf）
        result1 = deleter.delete_by_filename("content_list.pdf")
        print(result1)

        # 按文件名和页码删除
        result2 = deleter.delete_by_page_id("2.pdf", 1)
        print(result2)

    except Exception as e:
        print(f"删除异常: {str(e)}")