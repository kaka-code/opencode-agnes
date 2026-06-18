#!/usr/bin/env python3
"""Agnes AI 多轮对话 - 支持图片理解"""

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

API_BASE = "https://apihub.agnes-ai.com/v1"
DEFAULT_MODEL = "agnes-2.0-flash"

import sys

def print_colored(text, color_code):
    # 31 是红色，40 是黑色背景，1 是加粗
    reset = "\033[0m"
    print(f"\033[{color_code}m{text}{reset}")


def _image_to_data_uri(path):
    path = Path(path)
    ext = path.suffix.lstrip(".").lower()
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"data:image/{mime};base64,{b64}"


def _build_content(text, image=None):
    if not image:
        return text
    parts = [{"type": "text", "text": text}]
    for img in image:
        img_input = img
        if os.path.isfile(img):
            img_input = _image_to_data_uri(img)
        parts.append({"type": "image_url", "image_url": {"url": img_input}})
    return parts


def _call_api(api_key, model, messages, stream):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "stream": stream,
    }).encode()

    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    if stream:
        resp = urllib.request.urlopen(req, timeout=120)
        reply = ""
        for line in resp:
            line = line.decode().strip()
            if line.startswith("data: ") and line != "data: [DONE]":
                chunk = json.loads(line[6:])
                content = chunk["choices"][0].get("delta", {}).get("content", "")
                if content:
                    print(content, end="", flush=True)
                    reply += content
        print()
        return reply
    else:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        reply = result["choices"][0]["message"]["content"]
        print(reply)
        return reply


def main():
    parser = argparse.ArgumentParser(description="Agnes AI 多轮对话 - 支持图片理解")
    parser.add_argument("prompt", nargs="*", help="提示词")
    parser.add_argument("--api-key", help="API Key (默认从环境变量 AGNES_API_KEY 读取)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型名称 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--system", help="系统提示词")
    parser.add_argument("--stream", action="store_true", help="流式输出")
    parser.add_argument("--image", action="append", help="附加图片 (路径或URL，可多次使用)")
    parser.add_argument("--chat", action="store_true", help="多轮对话模式")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("错误: 请提供 API Key (通过 --api-key 或设置 AGNES_API_KEY 环境变量)", file=sys.stderr)
        sys.exit(1)

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})

    # --- 单轮模式 ---
    if not args.chat:
        prompt = " ".join(args.prompt) if args.prompt else sys.stdin.read().strip()
        if not prompt:
            print("错误: 请提供 prompt", file=sys.stderr)
            sys.exit(1)
        messages.append({"role": "user", "content": _build_content(prompt, args.image)})
        try:
            _call_api(api_key, args.model, messages, args.stream)
        except urllib.error.HTTPError as e:
            print(f"请求失败 ({e.code}): {e.read().decode()}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"请求失败: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # --- 多轮对话模式 ---
    if args.prompt:
        messages.append({"role": "user", "content": _build_content(" ".join(args.prompt), args.image)})
        try:
            reply = _call_api(api_key, args.model, messages, args.stream)
        except Exception as e:
            print(f"请求失败: {e}", file=sys.stderr)
            return
        messages.append({"role": "assistant", "content": reply})

    print("\n=== 多轮对话开始 (输入 /exit 退出, /image <路径> 附加图片) ===")
    while True:
        try:
            # 蓝色闪烁文字 (注意：某些终端不支持闪烁)
            print_colored("input:", "34;5")
            text = input(">>> ")
                # 绿色背景 + 白色文字 + 加粗
            print_colored("开始思考:", "1;37;42")

        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.strip() == "/exit":
            break

        if text.startswith("/image "):
            img_path = text[7:].strip()
            if args.image:
                args.image.append(img_path)
            else:
                args.image = [img_path]
            print(f"已添加图片: {img_path}")
            continue

        if not text.strip():
            continue

        images = args.image or None
        args.image = None

        messages.append({"role": "user", "content": _build_content(text, images)})
        try:
            reply = _call_api(api_key, args.model, messages, args.stream)
        except Exception as e:
            print(f"请求失败: {e}", file=sys.stderr)
            break
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
