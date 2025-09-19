import cv2
from paddleocr import PaddleOCR
import pprint

ocr = PaddleOCR(lang='ch')
img = cv2.imread('1.png')

result = ocr.predict(img)

print("返回类型：", type(result))
print("具体识别内容如下：")

result_dict = result[0]  # 取出字典

texts = result_dict['rec_texts']

full_text = '\n'.join(texts)
print("全文:\n", full_text)
