# 验证能否使用npu：7
import torch
from paddleocr import PaddleOCR

try:
    # 测试NPU:7是否可用
    device = torch.device('npu:7')
    print(f"Attempting to use NPU device: {device}")

    # 尝试初始化PaddleOCR并使用NPU:7
    ocr = PaddleOCR(
        lang='ch',
        use_textline_orientation=True,
    )
    print("Successfully initialized PaddleOCR with NPU:7")

except Exception as e:
    print(f"Error using NPU:7: {e}")
