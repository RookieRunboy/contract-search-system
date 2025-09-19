import PyPDF2
import io
from typing import List, Dict, Any

class SimplePDFExtractor:
    """
    简化的PDF文本提取器
    仅使用PyPDF2进行基础文本提取
    """

    def __init__(self):
        pass

    def extract_text(self, pdf_bytes: bytes, pdf_name: str = None) -> List[Dict[str, Any]]:
        """
        从PDF字节中提取文本信息
        
        参数:
        pdf_bytes (bytes): PDF文件的字节内容
        pdf_name (str, optional): PDF文件名
        
        返回:
        list: 包含每页文本信息的JSON格式列表
        """
        final_result = []
        
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            for page_index, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                
                # 改进空白页判断逻辑
                if not text or len(text.strip()) < 5:
                    page_text = "\n空白页"
                else:
                    page_text = text.strip()
                
                page_info = {
                    "pdf_name": pdf_name or "unknown",
                    "pageId": page_index,
                    "text": page_text
                }
                
                final_result.append(page_info)
        
        except Exception as e:
            print(f"PDF解析失败: {str(e)}")
            return [{
                "pdf_name": pdf_name or "unknown",
                "pageId": 1,
                "text": f"PDF解析失败：{str(e)}"
            }]
        
        # 如果没有提取到任何内容，返回错误信息
        if not final_result:
            return [{
                "pdf_name": pdf_name or "unknown",
                "pageId": 1,
                "text": "PDF解析失败：无法提取任何文本内容"
            }]
        
        return final_result