# 将图片发送给大模型进行多模态识别文本
from openai import OpenAI
import base64
import os
import json
from pdf2image import convert_from_path
import time
from PIL import Image
import io
import re
import shutil
import uuid
from pathlib import Path


class MultiModalTextExtractor:
    def __init__(self, api_key="sk-d728d228b2b14698a51a3c452c02cc7c"):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("API key is required.")

        # 使用Qwen的客户端配置
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
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

    def optimize_image(self, pil_image, max_size=700):
        """优化图像大小以减少token消耗"""
        # 转换为灰度 - 减少数据量
        pil_image = pil_image.convert('L')

        # 计算新尺寸，保持宽高比
        width, height = pil_image.size
        if max(width, height) > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))

            # 高质量下采样
            pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)

        return pil_image

    def encode_image(self, pil_image, max_size=700, quality=55):
        """将PIL图像编码为base64（带压缩参数）"""
        try:
            # 转换为灰度
            pil_image = pil_image.convert('L')

            # 调整尺寸
            width, height = pil_image.size
            if max(width, height) > max_size:
                ratio = max_size / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                pil_image = pil_image.resize(new_size, Image.LANCZOS)

            # 编码图像
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='JPEG', quality=quality)
            img_data = img_byte_arr.getvalue()

            # 验证和计算token
            Image.open(io.BytesIO(img_data)).verify()
            base64_data = base64.b64encode(img_data).decode("utf-8")

            print(f"压缩设置: {max_size}px/质量{quality} → {len(base64_data) // 4} tokens")

            return base64_data
        except Exception as e:
            raise ValueError(f"图片编码失败: {str(e)}")

    def extract_text_from_image(self, image, page_num):
        """使用Qwen从单张图片提取文本"""
        systemPrompt= (
            "角色：你是一位合同解析专家，接下来请你将给予的图像中的内容转换为文字\n"
            "输入：图像\n"
            "操作：将图像中的信息提取为文本信息,注意中英文符合与空格的处理\n"
            "输出：当前页的图片转换为的文本信息\n"
            "注意：仅返回识别出的文本内容，不需要任何额外内容\n"
        )

        # 初始压缩设置
        compression_levels = [
            {'max_size': 800, 'quality': 65},
            {'max_size': 700, 'quality': 55},
            {'max_size': 640, 'quality': 50},
            {'max_size': 512, 'quality': 40},
            {'max_size': 384, 'quality': 30}  # 最低可用质量
        ]

        last_error = None
        current_image = image.copy()

        for level in compression_levels:
            try:
                # 编码图像（使用当前压缩级别）
                base64_image = self.encode_image(
                    current_image,
                    max_size=level['max_size'],
                    quality=level['quality']
                )

                # 使用Qwen API进行识别
                completion = self.client.chat.completions.create(
                    model="qwen2.5-vl-32b-instruct",
                    messages=[
                        {
                            "role": "system",
                            "content": [{"type": "text", "text": systemPrompt}]
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                )

                text_content = completion.choices[0].message.content

                # 清理API返回的多余内容
                clean_text = re.sub(r'【.*?】', '', text_content)
                clean_text = clean_text.strip()

                # 空白页检测
                if len(clean_text) < 20:
                    # 检查是否包含合同常见元素
                    contract_keywords = ["甲方", "乙方", "条款", "第.*条", "签字", "盖章"]
                    if not any(re.search(kw, clean_text) for kw in contract_keywords):
                        return "空白页"

                return clean_text

            except Exception as e:
                last_error = e
                print(f"⚠️ 压缩级别 {level} 失败 (第{page_num}页): {str(e)}")
                continue

        # 所有压缩级别都尝试过仍失败
        error_msg = f"所有压缩尝试均失败 (第{page_num}页): {str(last_error)}"
        print(f"❌ {error_msg}")
        return f"ERROR: {error_msg}"

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

                # 避免API速率限制
                if page_num < len(images):
                    wait_time = 1  # 等待1秒确保不超过限制
                    time.sleep(wait_time)

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