import os
import json
import uuid
from pathlib import Path
from pdf2image import convert_from_bytes
import cv2
import numpy as np
from paddleocr import PaddleOCR
from typing import List, Dict, Any


class PaddleOCRPDFExtractor:
    """
    基于PaddleOCR的PDF文本提取器
    支持从PDF字节流中提取文本信息
    """
    
    def __init__(self, use_textline_orientation=True):
        """
        初始化PaddleOCR PDF提取器
        
        参数:
        use_textline_orientation (bool): 是否启用文字方向检测，默认为True
        """
        # 初始化 PaddleOCR，加载中文模型，开启文字方向检测
        self.ocr = PaddleOCR(
            lang='ch',
            use_textline_orientation=use_textline_orientation,
            device='cpu',
        )
    
    def pdf_bytes_to_images(self, pdf_bytes, dpi=180):
        """
        将PDF字节流转换为PIL图片列表
        
        参数:
        pdf_bytes (bytes): PDF文件的字节内容
        dpi (int): 转换分辨率，默认180
        
        返回:
        list: PIL图片列表
        """
        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                fmt='jpeg',
                thread_count=4,
                output_file=uuid.uuid4().hex
            )
            print(f"成功转换 {len(images)} 页")
            return images
        except Exception as e:
            print(f"PDF转换失败: {str(e)}")
            raise
    
    def extract_text_from_image(self, pil_image, page_num):
        """
        使用 PaddleOCR 从单页PIL图像提取文本
        
        参数:
        pil_image: PIL图像对象
        page_num (int): 页码
        
        返回:
        str: 提取的文本内容
        """
        try:
            # PIL转OpenCV BGR格式
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # 使用predict接口，返回列表，第一项是字典
            result = self.ocr.predict(img)
            
            # 取出字典
            result_dict = result[0]
            
            # 获取识别文本列表
            texts = result_dict.get('rec_texts', [])
            
            # 拼接所有文本
            full_text = '\n'.join(texts).strip()
            
            # 简单空白页检测
            if len(full_text) < 20:
                return "空白页"
            
            return full_text
            
        except Exception as e:
            print(f"第{page_num}页OCR识别失败: {str(e)}")
            return f"OCR识别失败: {str(e)}"
    
    def extract_text(self, pdf_bytes, pdf_name=None):
        """
        从PDF字节流中提取文本信息
        
        参数:
        pdf_bytes (bytes): PDF文件的字节内容
        pdf_name (str, optional): PDF文件名，如果未提供则使用默认名称
        
        返回:
        list: 包含每页文本信息的JSON格式列表
        """
        if pdf_name is None:
            pdf_name = "unknown_document"
        
        try:
            # 将PDF转换为图片
            images = self.pdf_bytes_to_images(pdf_bytes)
            results = []
            
            print(f"开始提取文本，共 {len(images)} 页...")
            
            for page_num, image in enumerate(images, start=1):
                print(f"处理第 {page_num}/{len(images)} 页...")
                
                # 提取文本
                page_text = self.extract_text_from_image(image, page_num)
                
                # 构建结果
                page_result = {
                    "pdf_name": pdf_name,
                    "pageId": page_num,
                    "text": page_text
                }
                
                results.append(page_result)
                print(f"第{page_num}页完成 ({len(page_text)}字符)")
            
            print(f"文本提取完成，共处理 {len(results)} 页")
            return results
            
        except Exception as e:
            print(f"PDF文本提取失败: {str(e)}")
            # 返回错误信息
            return [{
                "pdf_name": pdf_name,
                "pageId": 1,
                "text": f"PDF解析失败：{str(e)}"
            }]


if __name__ == "__main__":
    # 测试代码
    extractor = PaddleOCRPDFExtractor()
    
    # 测试PDF文件路径
    test_pdf_path = "/Users/runbo/Desktop/合同/C200C019D-华泰证券信息系统研发服务外包合同（2020.7.15至2021.7.14）.pdf"
    
    if os.path.exists(test_pdf_path):
        with open(test_pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        results = extractor.extract_text(pdf_bytes, "华泰证券合同")
        
        # 打印结果
        print(json.dumps(results[:2], ensure_ascii=False, indent=2))
    else:
        print(f"测试文件不存在: {test_pdf_path}")