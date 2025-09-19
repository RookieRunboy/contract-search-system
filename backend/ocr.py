import os
import time
import json
import shutil
import uuid
from pathlib import Path
from pdf2image import convert_from_path
import cv2
import numpy as np
from paddleocr import PaddleOCR


class MultiModalTextExtractor:
    def __init__(self, use_textline_orientation=False):
        # 初始化 PaddleOCR，加载中文模型，开启文字方向检测
        self.ocr = PaddleOCR(
            lang='ch',
            use_textline_orientation=True,
            device='cpu',
        )

    def pdf_to_images(self, pdf_path, dpi=180):
        """将PDF转换为PIL图片列表"""
        print(f"正在转换PDF: {pdf_path}")
        try:
            images = convert_from_path(
                pdf_path,
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

    def cleanup_temp_dir(self, temp_dir):
        """安全清理临时目录"""
        if os.path.exists(temp_dir):
            print(f"清理临时目录: {temp_dir}")
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"清理临时目录时出错: {str(e)}")

    def extract_text_from_image(self, pil_image, page_num):
        """使用 PaddleOCR 从单页PIL图像提取文本（基于ocr.predict）"""
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

    def process_contract(self, pdf_path, output_path):
        """处理PDF合同文件，逐页识别并保存文本结果为JSON"""
        start_time = time.time()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

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
                print(f"第{page_num}页完成 ({len(page_text)}字符)")

            except Exception as e:
                print(f"第{page_num}页失败: {str(e)}")
                results.append({
                    "pageId": page_num,
                    "text": f"ERROR: {str(e)}",
                })

        # 保存JSON结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        duration = time.time() - start_time
        success_count = sum(1 for r in results if not r.get("text", "").startswith("ERROR"))
        print(f"\n处理完成! 成功率: {success_count}/{len(images)}页")
        print(f"总耗时: {duration:.2f}秒")
        print(f"结果已保存至: {output_path}")

        return results


if __name__ == "__main__":
    input_dir = r"/data1/cyc/contract_search/contractSearchExamples/test1/"  # 输入PDF目录
    output_dir = r"output"  # 输出JSON目录

    os.makedirs(output_dir, exist_ok=True)

    extractor = MultiModalTextExtractor()

    pdf_files = [f for f in Path(input_dir).glob("*.pdf") if f.is_file()]

    if not pdf_files:
        print(f"在目录 {input_dir} 中未找到PDF文件")
    else:
        print(f"找到 {len(pdf_files)} 个PDF文件待处理:")

    for pdf_path in pdf_files:
        print(f"\n正在处理: {pdf_path.name}")
        try:
            output_path = Path(output_dir) / f"{pdf_path.stem}.json"
            results = extractor.process_contract(str(pdf_path), str(output_path))

            if results:
                success_pages = sum(1 for r in results if not r.get("text", "").startswith("ERROR"))
                print(f"处理完成! 成功率: {success_pages}/{len(results)}页")
                print(f"结果已保存至: {output_path}")

                print("\n第一页内容预览:")
                print(results[0]['text'][:500] + "...")
        except Exception as e:
            print(f"处理文件 {pdf_path.name} 时出错: {str(e)}")
