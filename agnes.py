#!/usr/bin/env python3
"""Agnes AI API 客户端 - 文本聊天或图片生成"""

import argparse
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("请先安装 openai: pip install openai", file=sys.stderr)
    sys.exit(1)

API_BASE = "https://apihub.agnes-ai.com/v1"
DEFAULT_MODEL = "agnes-image-2.0-flash"


def _download(url, path):
    import urllib.request
    urllib.request.urlretrieve(url, path)


def main():
    parser = argparse.ArgumentParser(description="调用 Agnes AI API")
    parser.add_argument("prompt", nargs="*", help="提示词")
    parser.add_argument("--api-key", help="API Key (默认从环境变量 AGNES_API_KEY 读取)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型名称 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--output", "-o", help="输出图片文件路径")
    parser.add_argument("--size", default="1024x768", help="图片尺寸 (默认: 1024x768)")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("错误: 请提供 API Key (通过 --api-key 或设置 AGNES_API_KEY 环境变量)", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(args.prompt) if args.prompt else sys.stdin.read().strip()
    if not prompt:
        print("错误: 请提供 prompt (作为参数或通过 stdin 传入)", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=API_BASE)

    is_image_model = "image" in args.model.lower()

    try:
        if is_image_model:
            response = client.images.generate(
                model=args.model,
                prompt=prompt,
                size=args.size,
            )
            image_url = response.data[0].url
            print(f"图片 URL: {image_url}")

            output_path = args.output or "agnes_output.jpg"
            _download(image_url, output_path)
            print(f"已保存: {output_path}")
        else:
            response = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "user", "content": prompt}],
            )
            print(response.choices[0].message.content)

    except Exception as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
