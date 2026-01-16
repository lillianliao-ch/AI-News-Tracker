#!/usr/bin/env python3
"""
AI 简历解析与评估 - 技术验证 Demo

功能：
1. 读取一个 PDF 简历
2. 使用 OpenAI 提取结构化信息
3. 评估匹配度（基于 JD 配置）
4. 打印详细结果

用法：
    python demo_ai_resume_parser.py --resume path/to/resume.pdf --openai-key sk-xxx
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("❌ 缺少依赖：pdfplumber")
    print("请运行：pip install pdfplumber")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("❌ 缺少依赖：openai")
    print("请运行：pip install openai")
    sys.exit(1)

# 支持通义千问（使用 OpenAI SDK 兼容模式）
QWEN_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class AIResumeParser:
    """AI 简历解析器"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", api_base: str = None):
        """
        初始化 AI 解析器
        
        Args:
            api_key: API Key（OpenAI 或 通义千问）
            model: 模型名称
            api_base: API 基础 URL（通义千问需要设置）
        """
        if api_base:
            # 使用通义千问或其他兼容 API
            self.client = OpenAI(api_key=api_key, base_url=api_base)
        else:
            # 使用 OpenAI
            self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def parse_pdf(self, pdf_path: str) -> str:
        """
        解析 PDF 简历，提取文本
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            提取的文本内容
        """
        print(f"\n📄 正在解析 PDF: {pdf_path}")
        
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        print(f"  ✅ 第 {i} 页解析完成（{len(page_text)} 字符）")
        except Exception as e:
            print(f"  ❌ PDF 解析失败: {e}")
            return ""
        
        print(f"  📊 总计提取 {len(text)} 字符")
        return text
    
    def extract_structure(self, resume_text: str) -> dict:
        """
        使用 OpenAI 提取结构化信息
        
        Args:
            resume_text: 简历文本
            
        Returns:
            结构化的简历数据
        """
        print("\n🤖 正在使用 AI 提取结构化信息...")
        
        prompt = """
你是一个专业的简历解析助手。
请从简历中提取以下信息，以JSON格式返回：

{
  "基本信息": {
    "姓名": "",
    "年龄": 0,
    "工作年限": 0,
    "当前公司": "",
    "当前职位": "",
    "学历": "",
    "毕业院校": "",
    "期望薪资": ""
  },
  "工作经历": [
    {
      "公司": "",
      "职位": "",
      "时间": "YYYY.MM-YYYY.MM",
      "工作内容": ["内容1", "内容2"],
      "核心成果": ["成果1", "成果2"]
    }
  ],
  "项目经验": [
    {
      "项目名称": "",
      "项目描述": "",
      "个人职责": "",
      "技术栈": ["技术1", "技术2"],
      "项目成果": ""
    }
  ],
  "技能清单": ["技能1", "技能2", "技能3"],
  "教育背景": [
    {
      "学校": "",
      "学历": "",
      "专业": "",
      "时间": "YYYY-YYYY"
    }
  ]
}

注意事项：
1. 如果某个字段在简历中找不到，填空字符串或0
2. 时间格式统一为 YYYY.MM 或 YYYY-YYYY
3. 工作年限按实际工作经历计算（不含实习）
4. 提取所有出现的技能关键词

简历内容：
""" + resume_text

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的简历解析助手，擅长提取结构化信息。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            print("  ✅ 结构化提取完成")
            return result
            
        except Exception as e:
            print(f"  ❌ AI 解析失败: {e}")
            return {}
    
    def evaluate_match(self, structured_resume: dict, jd_config: dict) -> dict:
        """
        评估候选人与 JD 的匹配度
        
        Args:
            structured_resume: 结构化简历
            jd_config: JD 配置
            
        Returns:
            评估结果
        """
        print("\n🎯 正在评估匹配度...")
        
        prompt = f"""
你是一个专业的猎头顾问。
请根据职位需求（JD）和候选人简历，评估匹配度。

【职位需求】
{json.dumps(jd_config, ensure_ascii=False, indent=2)}

【候选人简历】
{json.dumps(structured_resume, ensure_ascii=False, indent=2)}

请按以下维度评分（0-100分）：

1. **技能匹配度（权重40%）**
   - 核心技能覆盖率
   - 技能深度（年限、项目复杂度）
   - 加分技能

2. **经验匹配度（权重30%）**
   - 行业经验
   - 公司规模经验
   - 产品类型经验
   - 项目成果量化

3. **教育背景（权重15%）**
   - 学历匹配
   - 专业相关性
   - 学校档次

4. **稳定性（权重15%）**
   - 平均任职时长
   - 跳槽频率
   - 职业发展路径连贯性

输出JSON格式：
{{
  "技能匹配度": 85,
  "技能匹配分析": "候选人具备XXX技能...",
  "经验匹配度": 75,
  "经验匹配分析": "在XXX公司有X年经验...",
  "教育背景得分": 90,
  "教育分析": "XXX大学XXX专业...",
  "稳定性得分": 70,
  "稳定性分析": "平均任职X年...",
  "综合匹配度": 78,
  "推荐等级": "推荐 | 一般 | 不推荐",
  "核心优势": ["优势1", "优势2", "优势3"],
  "潜在风险": ["风险1", "风险2"],
  "推荐理由": "简短的推荐理由（50字以内）"
}}

评分标准：
- 综合匹配度 >= 75%  → "推荐"
- 综合匹配度 60-74% → "一般"
- 综合匹配度 < 60%  → "不推荐"
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的猎头顾问，擅长评估候选人匹配度。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            print("  ✅ 匹配度评估完成")
            return result
            
        except Exception as e:
            print(f"  ❌ 评估失败: {e}")
            return {}


def print_results(structured_resume: dict, evaluation: dict):
    """打印格式化的结果"""
    
    print("\n" + "="*80)
    print("📊 简历解析与评估结果")
    print("="*80)
    
    # 基本信息
    basic_info = structured_resume.get("基本信息", {})
    print("\n【基本信息】")
    print(f"  姓名: {basic_info.get('姓名', 'N/A')}")
    print(f"  年龄: {basic_info.get('年龄', 'N/A')}")
    print(f"  工作年限: {basic_info.get('工作年限', 'N/A')} 年")
    print(f"  当前公司: {basic_info.get('当前公司', 'N/A')}")
    print(f"  当前职位: {basic_info.get('当前职位', 'N/A')}")
    print(f"  学历: {basic_info.get('学历', 'N/A')}")
    print(f"  毕业院校: {basic_info.get('毕业院校', 'N/A')}")
    
    # 技能清单
    skills = structured_resume.get("技能清单", [])
    if skills:
        print(f"\n【技能清单】")
        print("  " + ", ".join(skills))
    
    # 工作经历
    work_exp = structured_resume.get("工作经历", [])
    if work_exp:
        print(f"\n【工作经历】（共 {len(work_exp)} 段）")
        for i, exp in enumerate(work_exp[:3], 1):  # 只显示前3段
            print(f"  {i}. {exp.get('公司', 'N/A')} - {exp.get('职位', 'N/A')}")
            print(f"     时间: {exp.get('时间', 'N/A')}")
    
    # 匹配度评估
    print("\n" + "-"*80)
    print("🎯 匹配度评估")
    print("-"*80)
    
    match_score = evaluation.get("综合匹配度", 0)
    recommend_level = evaluation.get("推荐等级", "未知")
    
    # 根据推荐等级显示不同颜色的图标
    level_icons = {
        "推荐": "✅",
        "一般": "⚠️",
        "不推荐": "❌"
    }
    icon = level_icons.get(recommend_level, "❓")
    
    print(f"\n  {icon} 推荐等级: {recommend_level}")
    print(f"  📊 综合匹配度: {match_score}%")
    print(f"\n  各维度得分：")
    print(f"    • 技能匹配度: {evaluation.get('技能匹配度', 0)}%")
    print(f"    • 经验匹配度: {evaluation.get('经验匹配度', 0)}%")
    print(f"    • 教育背景: {evaluation.get('教育背景得分', 0)}%")
    print(f"    • 稳定性: {evaluation.get('稳定性得分', 0)}%")
    
    # 核心优势
    strengths = evaluation.get("核心优势", [])
    if strengths:
        print(f"\n  💪 核心优势：")
        for strength in strengths:
            print(f"    ✓ {strength}")
    
    # 潜在风险
    risks = evaluation.get("潜在风险", [])
    if risks:
        print(f"\n  ⚠️  潜在风险：")
        for risk in risks:
            print(f"    • {risk}")
    
    # 推荐理由
    reason = evaluation.get("推荐理由", "")
    if reason:
        print(f"\n  📝 推荐理由：")
        print(f"    {reason}")
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="AI 简历解析与评估 Demo")
    parser.add_argument("--resume", required=True, help="PDF 简历路径")
    parser.add_argument("--api-key", required=True, help="API Key（OpenAI 或通义千问）")
    parser.add_argument("--model", default="qwen-turbo", help="模型名称（默认: qwen-turbo）")
    parser.add_argument("--provider", default="qwen", choices=["openai", "qwen"], 
                        help="API 提供商（默认: qwen）")
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(f"❌ 错误：文件不存在 {args.resume}")
        sys.exit(1)
    
    print("🚀 AI 简历解析与评估 Demo")
    print("="*80)
    
    # 示例 JD 配置（AI 产品经理）
    jd_config = {
        "职位名称": "AI产品经理（C端）",
        "工作地点": ["北京", "深圳"],
        "薪资范围": "30-60K",
        "工作年限": "3-5年",
        "学历要求": "本科及以上",
        "核心技能": [
            "AI产品经验（2年以上）",
            "C端产品（DAU>100万）",
            "大模型应用（RAG/Agent）"
        ],
        "加分技能": [
            "大厂背景（BAT/字节/美团等）",
            "0-1产品经验",
            "B端+C端复合背景"
        ],
        "评估权重": {
            "技能匹配": 0.40,
            "经验匹配": 0.30,
            "教育背景": 0.15,
            "稳定性": 0.15
        }
    }
    
    print("\n📋 使用的 JD 配置：")
    print(f"  职位: {jd_config['职位名称']}")
    print(f"  地点: {', '.join(jd_config['工作地点'])}")
    print(f"  薪资: {jd_config['薪资范围']}")
    print(f"  年限: {jd_config['工作年限']}")
    
    # 初始化解析器
    if args.provider == "qwen":
        print(f"\n🤖 使用 AI 服务: 通义千问 ({args.model})")
        ai_parser = AIResumeParser(
            api_key=args.api_key, 
            model=args.model,
            api_base=QWEN_API_BASE
        )
    else:
        print(f"\n🤖 使用 AI 服务: OpenAI ({args.model})")
        ai_parser = AIResumeParser(api_key=args.api_key, model=args.model)
    
    # 1. 解析 PDF
    resume_text = ai_parser.parse_pdf(args.resume)
    if not resume_text:
        print("❌ PDF 解析失败，程序退出")
        sys.exit(1)
    
    # 2. 提取结构化信息
    structured_resume = ai_parser.extract_structure(resume_text)
    if not structured_resume:
        print("❌ 结构化提取失败，程序退出")
        sys.exit(1)
    
    # 3. 评估匹配度
    evaluation = ai_parser.evaluate_match(structured_resume, jd_config)
    if not evaluation:
        print("❌ 匹配度评估失败，程序退出")
        sys.exit(1)
    
    # 4. 打印结果
    print_results(structured_resume, evaluation)
    
    # 5. 保存结果到 JSON 文件
    output_file = resume_path.stem + "_analysis.json"
    result = {
        "简历文件": str(resume_path),
        "JD配置": jd_config,
        "结构化简历": structured_resume,
        "评估结果": evaluation
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 完整结果已保存到: {output_file}")
    print("\n✅ Demo 运行完成！")


if __name__ == "__main__":
    main()

