from __future__ import annotations

"""
Quick Qwen3-VL health check.

Runs two requests to the configured Qwen endpoint:
1) Without Authorization header.
2) With Authorization header if QWEN_API_KEY is available.

Shows status codes and truncated responses to verify whether the API key is required
and whether the endpoint is reachable.
"""

import os
import textwrap
from typing import Dict, Tuple

import requests


def get_base_and_key() -> Tuple[str, str | None]:
    default_port = os.getenv("VLLM_PORT", "8000")
    default_base = f"http://qwen3-vl.sdflakjfajdhfaks.com:{default_port}/v1"
    api_base = (os.getenv("QWEN_API_BASE") or default_base).rstrip("/")
    api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    return api_base, api_key


def call_once(api_base: str, headers: Dict[str, str]) -> Tuple[int, str]:
    url = f"{api_base}/chat/completions"
    payload = {
        "model": os.getenv("QWEN_MM_MODEL", "qwen3vl"),
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": "ping"}]},
            {"role": "user", "content": [{"type": "text", "text": "你好"}]},
        ],
        "max_tokens": 16,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        preview = resp.text[:300].replace("\n", " ")
        return resp.status_code, preview
    except Exception as exc:  # noqa: BLE001
        return -1, f"exception: {exc}"


def main() -> None:
    api_base, api_key = get_base_and_key()
    print(f"Testing base: {api_base}")

    tests = [
        ("no-key", {}),
        ("with-key", {"Authorization": f"Bearer {api_key}"} if api_key else {}),
    ]

    for label, headers in tests:
        print(f"\n[{label}]")
        code, preview = call_once(api_base, headers)
        print(f"status: {code}")
        print("body  :")
        print(textwrap.indent(preview or "<empty>", prefix="  "))

    if api_key is None:
        print("\n提示: 未提供 QWEN_API_KEY/DASHSCOPE_API_KEY，本次只测试了无鉴权请求。")


if __name__ == "__main__":
    main()
