#!/usr/bin/env python3
"""
脉脉CV批量导入脚本 - 支持OCR（扫描版PDF）

需要安装OCR依赖：
pip install pdf2image pytesseract pillow
brew install tesseract  # macOS
brew install tesseract-lang  # 安装中文语言包
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目路径
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)
os.environ["DB_PATH"] = os.path.join(PROJECT_DIR, "data", "headhunter_dev.db")

def check_ocr_available():
    """检查OCR工具是否可用"""
    try:
        import pytesseract
        from pdf2image import convert_from_path

        # 检查tesseract
        result = subprocess.run(['tesseract', '--version'],
                                capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Tesseract未安装"

        return True, "OCR可用"
    except ImportError as e:
        return False, f"缺少依赖: {e}"

def extract_text_from_pdf_with_ocr(pdf_path: str) -> str:
    """
    从PDF中提取文本，支持OCR

    优先级：
    1. PyPDF2（文本PDF，快速）
    2. PyMuPDF（文本PDF，较快）
    3. OCR（扫描版PDF，慢但准确）
    """
    # 方法1: PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        if len(text.strip()) > 500:
            return text, "PyPDF2"
    except:
        pass

    # 方法2: PyMuPDF
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if len(text.strip()) > 500:
            return text, "PyMuPDF"
    except:
        pass

    # 方法3: OCR（扫描版）
    print("    📸 尝试OCR识别...")
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image

        # 将PDF转换为图片
        images = convert_from_path(pdf_path, dpi=200, fmt='jpeg')

        # 对每一页进行OCR
        all_text = []
        for i, image in enumerate(images, 1):
            print(f"      OCR第{i}/{len(images)}页...")
            # 使用中文语言包
            text = pytesseract.image_to_string(
                image,
                lang='chi_sim+eng',  # 简体中文+英文
                config='--psm 6'  # 假设单列文本
            )
            all_text.append(text)

        final_text = "\n".join(all_text)
        if len(final_text.strip()) > 100:
            return final_text, f"OCR({len(images)}页)"
        else:
            return final_text, "OCR(文本过少)"

    except ImportError as e:
        return "", f"OCR依赖缺失: {e}"
    except Exception as e:
        return "", f"OCR失败: {e}"

def test_single_file(pdf_path: str):
    """测试单个文件的OCR提取"""
    filename = os.path.basename(pdf_path)

    print("=" * 60)
    print(f"测试文件: {filename}")
    print("=" * 60)

    # 检查OCR
    available, message = check_ocr_available()
    if not available:
        print(f"❌ {message}")
        print("\n安装方法:")
        print("  pip install pdf2image pytesseract pillow")
        print("  brew install tesseract")
        print("  brew install tesseract-lang")
        return

    print(f"✅ {message}")

    # 提取文本
    print("\n提取文本...")
    text, method = extract_text_from_pdf_with_ocr(pdf_path)

    print(f"\n方法: {method}")
    print(f"字符数: {len(text)}")
    print(f"前500字符:")
    print("-" * 60)
    print(text[:500])
    print("-" * 60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='测试CV OCR提取')
    parser.add_argument('--file', help='CV文件路径')

    args = parser.parse_args()

    if args.file:
        test_single_file(args.file)
    else:
        # 测试默认文件
        test_file = "/Users/lillianliao/notion_rag/数据输入/0224cv/Alexdan-工作4年-【脉脉招聘】.pdf"
        test_single_file(test_file)
