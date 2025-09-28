# 基于本地 OCR (PaddleOCR) 进行合同文本识别
import os
import json
from pdf2image import convert_from_path
import time
import re
import shutil
import uuid
from pathlib import Path
import cv2
import numpy as np
from paddleocr import PaddleOCR


class MultiModalTextExtractor:
    def __init__(self, use_textline_orientation: bool = True, device: str = "cpu"):
        """初始化本地 OCR 引擎"""
        self.ocr = PaddleOCR(
            lang='ch',
            use_textline_orientation=use_textline_orientation,
            device=device,
        )

    def pdf_to_images(self, pdf_path, dpi=180):
        """将PDF转换为图像列表（避免临时文件问题）"""
        print(f"正在转换PDF: {pdf_path}")

        # 创建自定义临时目录
        # temp_dir = os.path.join(os.path.dirname(pdf_path), f"temp_{uuid.uuid4().hex}")
        # os.makedirs(temp_dir, exist_ok=True)

        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                output_folder=None,
                fmt='jpeg',
                thread_count=4,
                output_file=uuid.uuid4().hex
            )
            print(f"成功转换 {len(images)} 页")
            return images
        # finally:
        #     # 确保在函数结束时清理临时目录
        #     self.cleanup_temp_dir(temp_dir)
        except Exception as e:
            print(f"PDF转换失败: {str(e)}")
            raise

    def cleanup_temp_dir(self, temp_dir):
        """安全清理临时目录"""
        if os.path.exists(temp_dir):
            print(f"清理临时目录: {temp_dir}")
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"清理临时目录时出错: {str(e)}")

    def extract_text_from_image(self, image, page_num):
        """使用 PaddleOCR 从单页图像提取文本"""
        try:
            # 转换为 OpenCV BGR 图像
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # PaddleOCR 预测返回列表，第 0 项为包含识别结果的字典
            result = self.ocr.predict(img)
            result_dict = result[0] if result else {}
            texts = result_dict.get('rec_texts', []) if isinstance(result_dict, dict) else []

            clean_text = '\n'.join(texts).strip()

            # 空白页检测（保持与原逻辑一致）
            if len(clean_text) < 20:
                contract_keywords = ["甲方", "乙方", "条款", "第.*条", "签字", "盖章"]
                if not any(re.search(kw, clean_text) for kw in contract_keywords):
                    return "空白页"

            return clean_text or "空白页"

        except Exception as e:
            print(f"第{page_num}页OCR识别失败: {str(e)}")
            return f"ERROR: OCR识别失败 ({str(e)})"

    def process_contract(self, pdf_path, output_path):
        """处理整个PDF合同并保存结果"""
        start_time = time.time()

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 转换PDF为图像
        images = self.pdf_to_images(pdf_path)
        results = []

        print("开始文本提取...")
        for page_num, image in enumerate(images, start=1):
            print(f"处理第 {page_num}/{len(images)} 页...")
            try:
                page_text = self.extract_text_from_image(image, page_num)
                results.append({
                    "pageId": page_num,
                    "text": page_text
                })
                print(f"✅ 第{page_num}页完成 ({len(page_text)}字符)")

            except Exception as e:
                print(f"❌ 第{page_num}页失败: {str(e)}")
                results.append({
                    "pageId": page_num,
                    "text": f"ERROR: {str(e)}",
                    "status": "failed"
                })

        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 统计信息
        success_count = sum(1 for r in results if not r.get("text", "").startswith("ERROR"))
        duration = time.time() - start_time
        print(f"\n处理完成! 成功率: {success_count}/{len(images)}页")
        print(f"总耗时: {duration:.2f}秒")
        print(f"结果已保存至: {output_path}")

        return results


if __name__ == "__main__":
    # 路径配置
    input_dir = r"D:\Cyc\MyWork\testFiles\input"  # PDF输入目录
    output_dir = r"output"  # JSON输出目录

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 创建提取器实例
    extractor = MultiModalTextExtractor()

    # 获取input目录下所有PDF文件
    pdf_files = [f for f in Path(input_dir).glob("*.pdf") if f.is_file()]

    if not pdf_files:
        print(f"在目录 {input_dir} 中未找到PDF文件")
    else:
        print(f"找到 {len(pdf_files)} 个PDF文件待处理:")

    # 逐个处理PDF文件
    for pdf_path in pdf_files:
        try:
            print(f"\n正在处理: {pdf_path.name}")
            # if(pdf_path.name!= "C200C02EF招行格力智慧园区项目.pdf"):
            #     continue

            # 生成输出路径
            output_path = Path(output_dir) / f"{pdf_path.stem}.json"

            # 处理合同并保存结果
            results = extractor.process_contract(str(pdf_path), str(output_path))

            # 打印处理结果
            if results:
                success_pages = sum(1 for r in results if not r.get("text", "").startswith("ERROR"))
                print(f"处理完成! 成功率: {success_pages}/{len(results)}页")
                print(f"结果已保存至: {output_path}")

                # 打印第一页预览
                print("\n第一页内容预览:")
                print(results[0]['text'][:500] + "...")

        except Exception as e:
            print(f"处理文件 {pdf_path.name} 时出错: {str(e)}")
