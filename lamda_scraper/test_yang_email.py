#!/usr/bin/env python3
"""
直接测试杨嘉祺的邮箱提取
"""

import requests
import re

def get_yang_email():
    """从杨嘉祺的学术网站提取邮箱"""

    url = "https://academic.thyrixyang.com"

    # 请求网站
    response = requests.get(url, timeout=15)
    html = response.text

    # 查找 Cloudflare 编码的邮箱
    pattern = r'/cdn-cgi/l/email-protection#([a-fA-F0-9]+)'
    matches = re.findall(pattern, html)

    print(f"找到 {len(matches)} 个编码的邮箱\n")

    for i, encoded in enumerate(matches, 1):
        print(f"{i}. Encoded: {encoded}")

        # 尝试多种解码方法
        decoded = try_decode_methods(encoded)
        print(f"   Decoded: {decoded}\n")

def try_decode_methods(encoded_hex):
    """尝试多种解码方法"""

    methods = []

    # 方法1: 标准算法
    try:
        data = bytes.fromhex(encoded_hex)
        key = data[0]
        email1 = ''.join(chr(data[i] ^ (key >> 2)) for i in range(1, len(data)))
        methods.append(('标准算法', email1))
    except:
        pass

    # 方法2: 字节对组合
    try:
        data = bytes.fromhex(encoded_hex)
        key = data[0]
        email2 = ''
        for i in range(1, len(data), 2):
            if i + 1 < len(data):
                char = chr(data[i] ^ (key >> 2))
                email2 += char
        methods.append(('字节对', email2))
    except:
        pass

    # 方法3: 简单 XOR
    try:
        data = bytes.fromhex(encoded_hex)
        key = data[0]
        email3 = ''.join(chr(b ^ key) for b in data[1:])
        methods.append(('简单XOR', email3))
    except:
        pass

    # 打印所有方法的结果
    for name, result in methods:
        if '@' in result and '.' in result.split('@')[1]:
            return f"✓ {name}: {result}"
        else:
            pass

    # 返回最有希望的结果
    return methods[0][1] if methods else "无法解码"

if __name__ == '__main__':
    print("="*60)
    print("杨嘉祺邮箱提取测试")
    print("="*60)
    print()

    get_yang_email()
