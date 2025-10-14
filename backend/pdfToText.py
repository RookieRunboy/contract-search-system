from __future__ import annotations

import base64
import io
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from pdf2image import convert_from_path
from PIL import Image, ImageOps


class MultiModalTextExtractor:
    """使用通义千问多模态大模型识别合同文本的封装。"""

    DEFAULT_MODEL = "qwen3vl"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_COMPRESS_PRESETS: Tuple[Tuple[int, int], ...] = (
        (2200, 90),
        (1800, 85),
        (1500, 80),
        (1200, 75),
        (1000, 70),
    )

    SYSTEM_PROMPT = (
        "你是专业的合同解析助手。请将提供的合同页面转换为可阅读的中文段落，"
        "保留原有条款结构和编号，去除无关噪声。若页面为空或无法识别，"
        "请返回‘空白页’。"
    )

    CONTRACT_KEYWORDS = (
        "甲方",
        "乙方",
        "条款",
        "合同",
        "签字",
        "盖章",
        "服务",
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        self.api_key = api_key or os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")

        default_port = os.getenv("VLLM_PORT", "8000")
        default_base = f"http://qwen3-vl.sdflakjfajdhfaks.com:{default_port}/v1"
        self.api_base = (api_base or os.getenv("QWEN_API_BASE") or default_base).rstrip("/")

        if not self.api_key and "dashscope" in self.api_base:
            raise RuntimeError(
                "Qwen API key 未配置。请设置环境变量 QWEN_API_KEY 或 DASHSCOPE_API_KEY。"
            )
        self.model = model or os.getenv("QWEN_MM_MODEL") or self.DEFAULT_MODEL
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

    # ---------------------- 图像与压缩相关 ----------------------
    def pdf_to_images(self, pdf_path: Path, dpi: int = 220) -> List[Image.Image]:
        """将 PDF 转换为 PIL 图片列表。"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"未找到 PDF 文件: {pdf_path}")

        images = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            fmt="jpeg",
            thread_count=4,
            output_folder=None,
            use_pdftocairo=True,
        )
        return images

    def _iter_compressed_images(self, image: Image.Image) -> Iterable[Tuple[str, Dict[str, int]]]:
        """生成多档压缩后的 base64 图像。"""
        grayscale = ImageOps.grayscale(image)
        width, height = grayscale.size
        max_side = max(width, height)

        for target_side, quality in self.DEFAULT_COMPRESS_PRESETS:
            if max_side > target_side:
                scale = target_side / float(max_side)
                resized = grayscale.resize(
                    (int(width * scale), int(height * scale)),
                    resample=Image.LANCZOS,
                )
            else:
                resized = grayscale

            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=quality)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            yield encoded, {"max_side": target_side, "quality": quality}

    # ---------------------- 大模型调用 ----------------------
    def _call_vision_model(self, image_b64: str) -> str:
        """调用通义千问多模态接口。"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": self.SYSTEM_PROMPT},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请识别以下合同页面的全部文字内容。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                            },
                        },
                    ],
                },
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "top_p": 0.9,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code == 429 and attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)
                    continue

                response.raise_for_status()
                data = response.json()
                message = data.get("choices", [{}])[0].get("message", {})
                content = message.get("content")
                if isinstance(content, list):
                    text_parts = [part.get("text", "") for part in content if part.get("type") == "text"]
                    return "\n".join(text_parts).strip()
                if isinstance(content, str):
                    return content.strip()
                raise ValueError(f"未能解析接口返回内容: {data}")
            except (requests.RequestException, ValueError) as exc:
                if attempt == self.max_retries:
                    raise
                time.sleep(self.retry_delay * attempt)

        raise RuntimeError("模型接口调用失败")

    # ---------------------- 文本后处理 ----------------------
    @staticmethod
    def _cleanup_response(text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip()
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned)
        cleaned = cleaned.replace("```", "")
        cleaned = re.sub(r"\s+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _is_meaningful(self, text: str) -> bool:
        if not text or not text.strip():
            return False
        if len(text.strip()) >= 30:
            return True
        return any(keyword in text for keyword in self.CONTRACT_KEYWORDS)

    # ---------------------- 主流程 ----------------------
    def extract_text_from_image(self, image: Image.Image, page_num: int) -> str:
        last_text = ""
        last_error: Optional[Exception] = None

        for encoded, meta in self._iter_compressed_images(image):
            try:
                raw_text = self._call_vision_model(encoded)
                cleaned = self._cleanup_response(raw_text)
                if self._is_meaningful(cleaned):
                    return cleaned
                if cleaned:
                    last_text = cleaned
            except Exception as exc:  # noqa: BLE001 - 捕获后交给上层处理
                last_error = exc
                continue

        if last_text:
            return last_text
        if last_error:
            raise last_error
        return "空白页"

    def process_contract(
        self,
        pdf_path: Path,
        output_path: Optional[Path] = None,
        pdf_name: Optional[str] = None,
        dpi: int = 220,
    ) -> List[Dict[str, object]]:
        """识别整份合同并返回带页码的文本列表。"""
        pdf_path = Path(pdf_path)
        images = self.pdf_to_images(pdf_path, dpi=dpi)

        results: List[Dict[str, object]] = []
        start = time.time()

        for page_num, image in enumerate(images, start=1):
            try:
                text = self.extract_text_from_image(image, page_num)
                results.append(
                    {
                        "pdf_name": pdf_name or pdf_path.stem,
                        "pageId": page_num,
                        "text": text or "空白页",
                    }
                )
                print(f"✅ 第{page_num}页识别完成（{len(text)} 字符）")
            except Exception as exc:
                print(f"❌ 第{page_num}页识别失败: {exc}")
                results.append(
                    {
                        "pdf_name": pdf_name or pdf_path.stem,
                        "pageId": page_num,
                        "text": f"ERROR: {exc}",
                    }
                )

        duration = time.time() - start
        success_pages = sum(1 for item in results if not str(item.get("text", "")).startswith("ERROR"))
        print(f"处理完成，成功 {success_pages}/{len(results)} 页，总耗时 {duration:.2f} 秒")

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"识别结果已保存：{output_path}")

        return results

    def extract_pdf_bytes(
        self,
        pdf_bytes: bytes,
        pdf_name: Optional[str] = None,
        dpi: int = 220,
    ) -> List[Dict[str, object]]:
        """直接处理 PDF 字节内容。"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = Path(tmp_file.name)

        try:
            return self.process_contract(tmp_path, output_path=None, pdf_name=pdf_name, dpi=dpi)
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="调用通义千问识别 PDF 合同文本")
    parser.add_argument("pdf", type=str, help="待识别的 PDF 路径")
    parser.add_argument("--output", type=str, default="output/result.json", help="识别结果输出路径")
    parser.add_argument("--dpi", type=int, default=220, help="渲染 PDF 的 DPI")
    args = parser.parse_args()

    extractor = MultiModalTextExtractor()
    extractor.process_contract(Path(args.pdf), Path(args.output), dpi=args.dpi)
