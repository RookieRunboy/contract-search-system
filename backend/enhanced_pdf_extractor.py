import os
from typing import List, Dict, Any

import cv2
import fitz
import numpy as np
from pdf2image import convert_from_bytes


class EnhancedPDFExtractor:
    """
    结合 PyMuPDF 与可选 PaddleOCR 的PDF文本提取器。
    默认优先使用 PyMuPDF 提取文本；若需要OCR请设置
    环境变量 ENABLE_PADDLE_OCR=1 以启用 PaddleOCR 识别。
    """

    def __init__(self) -> None:
        env_flag = os.getenv("ENABLE_PADDLE_OCR", "1").lower()
        self.enable_ocr = env_flag not in {"0", "false", "no"}
        self.ocr = None

        if self.enable_ocr:
            try:
                from paddleocr import PaddleOCR  # 延迟导入，避免不必要的初始化

                self.ocr = PaddleOCR(
                    lang='ch',
                    use_textline_orientation=True,
                    device='cpu',
                )
            except Exception as exc:
                print(f"警告: PaddleOCR 初始化失败，将回退到 PyMuPDF 文本提取。错误: {exc}")
                self.enable_ocr = False
                self.ocr = None

    def extract_text_pymupdf(self, pdf_bytes: bytes) -> List[str]:
        """使用 PyMuPDF 从PDF提取文本（逐页）。"""
        texts: List[str] = []
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page_index in range(doc.page_count):
                    page = doc.load_page(page_index)
                    page_text = page.get_text("text") or ""
                    texts.append(page_text.strip())
        except Exception as exc:
            print(f"PyMuPDF文本提取失败: {exc}")
        return texts

    def pdf_bytes_to_images(self, pdf_bytes: bytes, dpi: int = 180) -> List[np.ndarray]:
        """将PDF字节流转换为OpenCV可用的图像列表。"""
        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                fmt='jpeg',
            )
            return [cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR) for image in images]
        except Exception as exc:
            print(f"PDF转图片失败: {exc}")
            return []

    def extract_text_ocr(self, pdf_bytes: bytes, max_pages: int = None) -> List[str]:
        """使用 PaddleOCR 提取文本。若未启用OCR则返回空列表。"""
        if not self.enable_ocr or self.ocr is None:
            return []

        try:
            images = self.pdf_bytes_to_images(pdf_bytes)
            if not images:
                return []

            if max_pages:
                images = images[:max_pages]

            texts: List[str] = []
            for page_num, cv_image in enumerate(images, 1):
                print(f"正在OCR识别第{page_num}页...")
                result = self.ocr.ocr(cv_image)

                page_text = ""
                if result and result[0]:
                    for line in result[0]:
                        if len(line) >= 2:
                            text = line[1][0]
                            confidence = line[1][1]
                            if confidence > 0.5:
                                page_text += text + "\n"
                texts.append(page_text.strip())

            return texts
        except Exception as exc:
            print(f"OCR识别失败: {exc}")
            return []

    def extract_text(self, pdf_bytes: bytes, pdf_name: str = None) -> List[Dict[str, Any]]:
        """综合提取逻辑：先尝试 PyMuPDF，再按需回退到OCR。"""
        texts: List[str] = []
        meaningful: List[str] = []

        if self.enable_ocr:
            texts = self.extract_text_ocr(pdf_bytes)
            meaningful = [text for text in texts if text and text.strip()]
            if meaningful:
                print("已使用PaddleOCR完成文本识别")

        if not meaningful:
            pymupdf_texts = self.extract_text_pymupdf(pdf_bytes)
            meaningful = [text for text in pymupdf_texts if text and text.strip()]
            if meaningful:
                texts = pymupdf_texts
                if self.enable_ocr:
                    print("PaddleOCR未获取有效文本，回退至PyMuPDF提取")
            elif not self.enable_ocr:
                print("PyMuPDF未提取到有效内容。如需OCR识别，请设置 ENABLE_PADDLE_OCR=1 后重试。")

        final_result: List[Dict[str, Any]] = []
        for page_index, text in enumerate(texts, 1):
            page_text = text.strip() if text and text.strip() else "\n空白页"
            final_result.append({
                "pdf_name": pdf_name or "unknown",
                "pageId": page_index,
                "text": page_text
            })

        if not final_result:
            final_result = [{
                "pdf_name": pdf_name or "unknown",
                "pageId": 1,
                "text": "PDF解析失败：无法提取任何文本内容"
            }]

        return final_result
