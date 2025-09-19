import PyPDF2
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import io
from typing import List, Dict, Any
from PIL import Image

class EnhancedPDFExtractor:
    """
    增强的PDF文本提取器
    支持多种提取方式：PyPDF2、pdfplumber、OCR
    """

    def __init__(self):
        # 设置tesseract路径（如果需要）
        # pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        pass

    def extract_text_pypdf2(self, pdf_bytes: bytes) -> List[str]:
        """使用PyPDF2提取文本"""
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            texts = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                texts.append(text if text else "")
            
            return texts
        except Exception as e:
            print(f"PyPDF2提取失败: {str(e)}")
            return []

    def extract_text_pdfplumber(self, pdf_bytes: bytes) -> List[str]:
        """使用pdfplumber提取文本"""
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            texts = []
            
            with pdfplumber.open(pdf_stream) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    texts.append(text if text else "")
            
            return texts
        except Exception as e:
            print(f"pdfplumber提取失败: {str(e)}")
            return []

    def extract_text_ocr(self, pdf_bytes: bytes, max_pages: int = 5) -> List[str]:
        """使用OCR提取文本（限制页数以避免过长处理时间）"""
        try:
            # 将PDF转换为图片
            images = convert_from_bytes(pdf_bytes, first_page=1, last_page=max_pages)
            texts = []
            
            for i, image in enumerate(images):
                print(f"正在OCR识别第{i+1}页...")
                # 使用tesseract进行OCR识别
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                texts.append(text if text else "")
            
            return texts
        except Exception as e:
            print(f"OCR提取失败: {str(e)}")
            return []

    def extract_text(self, pdf_bytes: bytes, pdf_name: str = None) -> List[Dict[str, Any]]:
        """
        智能提取PDF文本，按优先级尝试不同方法
        
        参数:
        pdf_bytes (bytes): PDF文件的字节内容
        pdf_name (str, optional): PDF文件名
        
        返回:
        list: 包含每页文本信息的JSON格式列表
        """
        final_result = []
        
        # 方法1: 尝试PyPDF2
        print("尝试使用PyPDF2提取文本...")
        texts_pypdf2 = self.extract_text_pypdf2(pdf_bytes)
        
        # 方法2: 尝试pdfplumber
        print("尝试使用pdfplumber提取文本...")
        texts_pdfplumber = self.extract_text_pdfplumber(pdf_bytes)
        
        # 选择最佳结果
        texts = []
        if texts_pypdf2 and any(len(text.strip()) > 10 for text in texts_pypdf2):
            texts = texts_pypdf2
            print("使用PyPDF2提取结果")
        elif texts_pdfplumber and any(len(text.strip()) > 10 for text in texts_pdfplumber):
            texts = texts_pdfplumber
            print("使用pdfplumber提取结果")
        else:
            # 方法3: 使用OCR（仅处理前5页）
            print("文本提取失败，尝试OCR识别（仅前5页）...")
            texts = self.extract_text_ocr(pdf_bytes, max_pages=5)
        
        # 构建结果
        for page_index, text in enumerate(texts, 1):
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
        
        # 如果没有提取到任何内容，返回错误信息
        if not final_result:
            return [{
                "pdf_name": pdf_name or "unknown",
                "pageId": 1,
                "text": "PDF解析失败：无法提取任何文本内容"
            }]
        
        return final_result