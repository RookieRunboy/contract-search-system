from pdfToText import MultiModalTextExtractor
from PIL import Image


def main():
    extractor = MultiModalTextExtractor()
    image_path = "1.png"  # 将此路径替换为实际图片位置

    try:
        pil_image = Image.open(image_path)
        text = extractor.extract_text_from_image(pil_image, page_num=1)
        print(text)
    except FileNotFoundError:
        print(f"未找到图像文件: {image_path}")


if __name__ == "__main__":
    main()
