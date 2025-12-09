import logging
import re
from typing import Dict, List

try:
    import PyPDF2  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - 环境缺少PyPDF2时延迟报错
    PyPDF2 = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """文档处理器，用于处理PDF文档并分块"""

    def __init__(self, chunk_size: int = 2500, chunk_overlap: int = 250):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be zero or a positive integer")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_document(self, file_path: str, filename: str) -> List[Dict]:
        """处理文档并返回分块结果"""
        try:
            text = self._extract_pdf_text(file_path)
            cleaned_text = self._clean_text(text)
            chunks = self._split_text_into_chunks(
                cleaned_text,
                self.chunk_size,
                self.chunk_overlap,
            )

            document_chunks: List[Dict[str, object]] = []
            for i, chunk in enumerate(chunks):
                document_chunks.append(
                    {
                        "content": chunk,
                        "filename": filename,
                        "chunk_id": i,
                        "page_number": i + 1,  # 简化的页码处理
                    }
                )

            logger.info("文档 %s 处理完成，共生成 %d 个块", filename, len(document_chunks))
            return document_chunks

        except Exception as exc:  # noqa: BLE001 - 记录并重新抛出具体异常
            logger.error("处理文档 %s 时出错: %s", filename, str(exc))
            raise

    def _extract_pdf_text(self, file_path: str) -> str:
        """从PDF文件中提取文本"""
        text = ""
        try:
            if PyPDF2 is None:
                raise ImportError(
                    "PyPDF2 未安装，请运行 'pip install PyPDF2' 或在 requirements 中添加它"
                )
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += (page.extract_text() or "") + "\n"
        except Exception as exc:  # noqa: BLE001 - 记录并重新抛出具体异常
            logger.error("PDF文本提取失败: %s", str(exc))
            raise
        return text

    def _clean_text(self, text: str) -> str:
        """清理文本，移除多余的空白字符"""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", text)
        return text.strip()

    def _split_text_into_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        """使用滑动窗口机制将文本分割成块"""
        if not text:
            return []

        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be zero or a positive integer")

        step = max(1, chunk_size - chunk_overlap)
        chunks: List[str] = []
        text_length = len(text)
        start = 0

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_length:
                break
            start += step

        return chunks
