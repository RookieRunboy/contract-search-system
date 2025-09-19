import PyPDF2
import io
from typing import List, Dict, Any

class SimplePDFExtractor:
    """
    简单的PDF文本提取器
    使用PyPDF2库从PDF字节中提取文本信息
    """

    def __init__(self):
        pass

    def extract_text(self, pdf_bytes: bytes, pdf_name: str = None) -> List[Dict[str, Any]]:
        """
        从PDF字节中提取文本信息

        参数:
        pdf_bytes (bytes): PDF文件的字节内容
        pdf_name (str, optional): PDF文件名，如果未提供则使用默认名称

        返回:
        list: 包含每页文本信息的JSON格式列表
        """
        try:
            # 创建字节流
            pdf_stream = io.BytesIO(pdf_bytes)
            
            # 创建PDF阅读器
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            # 存储最终结果的列表
            final_result = []
            
            # 遍历每一页
            for page_index, page in enumerate(pdf_reader.pages, 1):
                try:
                    # 提取页面文本
                    page_text = page.extract_text()
                    
                    # 空白页处理
                    if not page_text or len(page_text.strip()) < 10:
                        page_text = "\n空白页"
                    
                    # 构建每页的字典
                    page_info = {
                        "pdf_name": pdf_name or "unknown",
                        "pageId": page_index,
                        "text": page_text.strip()
                    }
                    
                    final_result.append(page_info)
                    
                except Exception as e:
                    print(f"处理第{page_index}页时出错: {str(e)}")
                    # 即使某页出错，也添加一个空页记录
                    page_info = {
                        "pdf_name": pdf_name or "unknown",
                        "pageId": page_index,
                        "text": f"页面解析错误: {str(e)}"
                    }
                    final_result.append(page_info)
            
            return final_result
            
        except Exception as e:
            print(f"PDF解析失败: {str(e)}")
            # 返回错误信息
            return [{
                "pdf_name": pdf_name or "unknown",
                "pageId": 1,
                "text": f"PDF解析失败: {str(e)}"
            }]