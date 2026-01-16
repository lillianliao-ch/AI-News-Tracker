#!/usr/bin/env python3
"""
测试 PyPDF2 解析简历的效果
"""
import PyPDF2
import json

def parse_resume_with_pypdf2(pdf_path):
    """使用 PyPDF2 解析 PDF"""
    print(f"\n{'='*60}")
    print(f"📄 测试文件: {pdf_path}")
    print(f"{'='*60}\n")

    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)

            # 基本信息
            num_pages = len(pdf_reader.pages)
            print(f"📊 页数: {num_pages}")

            # 提取文本
            print(f"\n📝 提取的文本（前 500 字符）:")
            print("-" * 60)
            full_text = ""
            for i, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                full_text += text + "\n"
                if i == 0:
                    print(text[:500] + "...")

            print(f"\n📏 总文本长度: {len(full_text)} 字符")

            # 元数据
            metadata = pdf_reader.metadata
            if metadata:
                print(f"\n📋 元数据:")
                print(f"  作者: {metadata.get('/Author', '未知')}")
                print(f"  创建时间: {metadata.get('/CreationDate', '未知')}")
                print(f"  修改时间: {metadata.get('/ModDate', '未知')}")

            # 保存原始文本
            output_path = pdf_path.replace('.pdf', '_pypdf2_output.txt')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"\n💾 原始文本已保存到: {output_path}")

            return {
                'method': 'PyPDF2',
                'num_pages': num_pages,
                'text_length': len(full_text),
                'text_preview': full_text[:500],
                'metadata': str(metadata) if metadata else None
            }

    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


if __name__ == "__main__":
    import sys

    pdf_path = "/Users/lillianliao/Desktop/CV_ZhanzhaoLIANG_20251016.pdf"

    result = parse_resume_with_pypdf2(pdf_path)

    # 保存结果
    if result:
        with open('/Users/lillianliao/Desktop/pypdf2_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 测试结果已保存到: /Users/lillianliao/Desktop/pypdf2_test_result.json")
