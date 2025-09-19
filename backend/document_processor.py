import PyPDF2
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文档处理器，用于处理PDF文档并分块"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_document(self, file_path: str, filename: str) -> List[Dict]:
        """处理文档并返回分块结果"""
        try:
            # 提取PDF文本
            text = self._extract_pdf_text(file_path)
            
            # 清理文本
            cleaned_text = self._clean_text(text)
            
            # 分块
            chunks = self._split_text_into_chunks(cleaned_text)
            
            # 构建文档块
            document_chunks = []
            for i, chunk in enumerate(chunks):
                document_chunks.append({
                    'content': chunk,
                    'filename': filename,
                    'chunk_id': i,
                    'page_number': i + 1  # 简化的页码处理
                })
            
            logger.info(f"文档 {filename} 处理完成，共生成 {len(document_chunks)} 个块")
            return document_chunks
            
        except Exception as e:
            logger.error(f"处理文档 {filename} 时出错: {str(e)}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """从PDF文件中提取文本"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF文本提取失败: {str(e)}")
            raise
        return text
    
    def _clean_text(self, text: str) -> str:
        """清理文本，移除多余的空白字符"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        return text.strip()
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """将文本分割成块"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在句号处分割
            if end < len(text):
                # 寻找最近的句号
                last_period = text.rfind('。', start, end)
                if last_period != -1 and last_period > start + self.chunk_size // 2:
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 计算下一个块的起始位置（考虑重叠）
            start = max(start + self.chunk_size - self.chunk_overlap, end)
        
        return chunks