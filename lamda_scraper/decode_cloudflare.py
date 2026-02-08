#!/usr/bin/env python3
"""
使用 JavaScript 解码 Cloudflare 邮件保护
"""

import subprocess
import json

def decode_cloudflare_email(encoded_hex):
    """
    使用 Node.js JavaScript 引擎解码 Cloudflare 邮件

    Args:
        encoded_hex: 编码的 hex 字符串

    Returns:
        解码后的邮箱
    """
    js_code = f"""
    const encoded = "{encoded_hex}";

    // Cloudflare 邮件解码算法
    function decodeCloudflareEmail(encoded) {{
        const data = Buffer.from(encoded, 'hex');
        const key = data[0];
        let email = '';

        for (let i = 1; i < data.length; i++) {{
            email += String.fromCharCode(data[i] ^ (key >> 2));
        }}

        return email;
    }}

    console.log(decodeCloudflareEmail(encoded));
    """

    try:
        result = subprocess.run(
            ['node', '-e', js_code],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    # 测试
    encoded = "d7a3bfaea5beafaeb6b9b097b0bab6bebbf9b4b8ba"
    decoded = decode_cloudflare_email(encoded)

    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")

if __name__ == '__main__':
    main()
