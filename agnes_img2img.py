#!/usr/bin/env python3
"""Agnes AI 图生图 - 上传图片 + prompt 修改图片并输出"""

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

API_BASE = "https://apihub.agnes-ai.com/v1"
DEFAULT_MODEL = "agnes-image-2.1-flash"


def _image_to_data_uri(path):
    path = Path(path)
    ext = path.suffix.lstrip(".").lower()
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"data:image/{mime};base64,{b64}"


def main():
    parser = argparse.ArgumentParser(description="Agnes AI 图生图 - 用图片+prompt生成新图片")
    parser.add_argument("--image", required=True, help="输入图片路径 (本地文件或公网 URL)")
    parser.add_argument("--prompt", required=True, help="修改图片的描述")
    parser.add_argument("--api-key", help="API Key (默认从环境变量 AGNES_API_KEY 读取)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型名称 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--output", "-o", default="agnes_edited.jpg", help="输出图片路径 (默认: agnes_edited.jpg)")
    parser.add_argument("--size", default="1024x768", help="图片尺寸 (默认: 1024x768)")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("错误: 请提供 API Key (通过 --api-key 或设置 AGNES_API_KEY 环境变量)", file=sys.stderr)
        sys.exit(1)

    image_input = args.image
    if os.path.isfile(image_input):
        print(f"读取本地图片: {image_input}")
        image_input = _image_to_data_uri(image_input)

    body = json.dumps({
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "extra_body": {
            "image": [image_input],
            "response_format": "url",
        },
    }).encode()

    req = urllib.request.Request(
        f"{API_BASE}/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"请求失败 ({e.code}): {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    image_url = result["data"][0]["url"]
    print(f"生成图片 URL: {image_url}")

    urllib.request.urlretrieve(image_url, args.output)
    print(f"已保存: {args.output}")


if __name__ == "__main__":
    main()
