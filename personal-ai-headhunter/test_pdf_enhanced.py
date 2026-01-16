#!/usr/bin/env python3
"""
增强版 PDF 解析（模拟 PDF Skill 的效果）
使用多个库组合，提高解析质量
"""
import json
import re
from pathlib import Path

def parse_resume_enhanced(pdf_path):
    """增强版 PDF 解析"""
    print(f"\n{'='*60}")
    print(f"📄 增强版 PDF 解析")
    print(f"文件: {pdf_path}")
    print(f"{'='*60}\n")

    # 先用 PyPDF2 提取
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
    except Exception as e:
        print(f"❌ PyPDF2 错误: {e}")
        return None

    # 清洗和格式化文本
    cleaned_text = clean_resume_text(full_text)

    # 提取结构化信息
    structured_data = extract_structured_info(cleaned_text)

    # 保存清洗后的文本
    output_path = pdf_path.replace('.pdf', '_enhanced_output.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)

    # 保存结构化数据
    json_output = pdf_path.replace('.pdf', '_enhanced_structured.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 清洗后的文本: {output_path}")
    print(f"✅ 结构化数据: {json_output}")
    print(f"\n📊 提取的结构化信息:")
    print(json.dumps(structured_data, ensure_ascii=False, indent=2))

    return structured_data


def clean_resume_text(text):
    """清洗简历文本"""
    # 修复特殊字符（常见问题）
    char_map = {
        '⼯': '工', '⾳': '音', '⽤': '用', '⼈': '人',
        '⼤': '天', '⽬': '前', '⼩': '小', '余': '余',
        '⽬': '目', '的': '的', '了': '了'
    }

    for bad, good in char_map.items():
        text = text.replace(bad, good)

    # 修复换行符
    text = re.sub(r'\n+', '\n', text)

    # 在关键字段前添加换行
    text = re.sub(r'工作经验', '\n工作经验', text)
    text = re.sub(r'工作内容', '\n工作内容', text)
    text = re.sub(r'工作成果', '\n工作成果', text)
    text = re.sub(r'教育背景', '\n教育背景', text)
    text = re.sub(r'学历', '\n学历', text)
    text = re.sub(r'学位', '\n学位', text)

    # 修复时间格式（03/2025 → 2025-03）
    text = re.sub(r'(\d{2})/(\d{4})', r'\2-\1', text)

    # 修复项目列表（o → •）
    text = re.sub(r'\so\s+', '\n• ', text)

    return text.strip()


def extract_structured_info(text):
    """提取结构化信息"""
    result = {
        'basic_info': {},
        'work_experience': [],
        'education': [],
        'skills': []
    }

    # 提取姓名（通常是第一个词）
    lines = text.split('\n')
    if lines:
        result['basic_info']['name'] = lines[0].strip()

    # 提取电话和邮箱
    phone_match = re.search(r'电话[：:]\s*(\d{11}|\d{3,4}[-\s]\d{7,8})', text)
    if phone_match:
        result['basic_info']['phone'] = phone_match.group(1)

    email_match = re.search(r'邮箱[：:]\s*([\w\.-]+@[\w\.-]+\.\w+)', text)
    if email_match:
        result['basic_info']['email'] = email_match.group(1)

    # 提取工作经历
    work_pattern = r'(\d{4}-\d{2}|\d{2}/\d{4})\s*[-~到]*\s*(\d{4}-\d{2}|\d{2}/\d{4}|现在|现在)\s*[,，]?\s*([^,，\n]+?)\s*[,，]\s*([^,，\n]+?)(?=[\n]|$|•)'

    work_matches = re.finditer(work_pattern, text)
    for match in work_matches:
        start_time = match.group(1)
        end_time = match.group(2)
        company_title = match.group(3).strip()
        description = match.group(4).strip()

        # 分离公司和职位
        if ',' in company_title:
            parts = company_title.split(',')
            company = parts[0].strip()
            title = ','.join(parts[1:]).strip()
        else:
            company = company_title
            title = ""

        result['work_experience'].append({
            'start_time': start_time,
            'end_time': end_time,
            'company': company,
            'title': title,
            'description': description
        })

    # 提取教育背景
    edu_pattern = r'学位[：:]\s*([^,，\n]+?),\s*([^\n]+?)\s*学校\s*([^\n]+?)\s*时间\s*([\d/\s-]+)'

    edu_matches = re.finditer(edu_pattern, text)
    for match in edu_matches:
        degree = match.group(1).strip()
        major = match.group(2).strip()
        school = match.group(3).strip()
        time = match.group(4).strip()

        result['education'].append({
            'degree': degree,
            'major': major,
            'school': school,
            'time': time
        })

    # 提取技能（常见技术栈关键词）
    tech_keywords = [
        'Python', 'Java', 'C\\+\\+', 'Go', 'JavaScript', 'TypeScript',
        'React', 'Vue', 'Angular', 'Node.js', 'Spring Boot',
        'PyTorch', 'TensorFlow', 'Keras', 'Scikit-learn',
        'Docker', 'Kubernetes', 'Linux', 'SQL', 'NoSQL',
        'Scala', 'Spark', 'Hadoop', 'AWS', 'Azure', 'GCP',
        'LLM', 'NLP', 'CV', '机器学习', '深度学习', '人工智能'
    ]

    for keyword in tech_keywords:
        if re.search(keyword, text, re.IGNORECASE):
            result['skills'].append(keyword)

    return result


if __name__ == "__main__":
    pdf_path = "/Users/lillianliao/Desktop/CV_ZhanzhaoLIANG_20251016.pdf"

    result = parse_resume_enhanced(pdf_path)

    if result:
        print(f"\n{'='*60}")
        print(f"📊 解析统计")
        print(f"{'='*60}")
        print(f"✅ 提取基本信息: {len(result['basic_info'])} 个字段")
        print(f"✅ 提取工作经历: {len(result['work_experience'])} 段")
        print(f"✅ 提取教育背景: {len(result['education'])} 段")
        print(f"✅ 提取技能标签: {len(result['skills'])} 个")
