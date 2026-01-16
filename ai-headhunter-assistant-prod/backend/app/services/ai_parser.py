"""
AI 简历解析服务

功能：
1. PDF 解析
2. 结构化信息提取（OpenAI/通义千问）
3. 匹配度评估
"""

import base64
import json
from io import BytesIO
from typing import Dict, Any, Optional
import pdfplumber
from openai import OpenAI


class AIResumeParser:
    """AI 简历解析器"""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "qwen-turbo",
        provider: str = "qwen"
    ):
        """
        初始化 AI 解析器
        
        Args:
            api_key: API Key
            model: 模型名称
            provider: API 提供商（qwen/openai）
        """
        if provider == "qwen":
            # 通义千问
            api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self.client = OpenAI(api_key=api_key, base_url=api_base)
        elif provider == "openai":
            # OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.model = model
        self.provider = provider
    
    def parse_pdf_from_base64(self, base64_data: str) -> str:
        """
        从 Base64 数据解析 PDF
        
        Args:
            base64_data: Base64 编码的 PDF 数据
            
        Returns:
            提取的文本内容
        """
        try:
            # 解码 Base64
            pdf_bytes = base64.b64decode(base64_data)
            pdf_file = BytesIO(pdf_bytes)
            
            # 提取文本
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text
        
        except Exception as e:
            raise ValueError(f"PDF 解析失败: {str(e)}")
    
    def extract_structure(self, resume_text: str) -> Dict[str, Any]:
        """
        使用 AI 提取结构化信息
        
        Args:
            resume_text: 简历文本
            
        Returns:
            结构化的简历数据
        """
        # 限制文本长度（避免超过 token 限制）
        if len(resume_text) > 8000:
            resume_text = resume_text[:8000]
        
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
            return result
            
        except Exception as e:
            raise ValueError(f"AI 解析失败: {str(e)}")
    
    def evaluate_match(
        self, 
        structured_resume: Dict[str, Any], 
        jd_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估候选人与 JD 的匹配度
        
        Args:
            structured_resume: 结构化简历
            jd_config: JD 配置
            
        Returns:
            评估结果
        """
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
  "推荐理由": "简短的推荐理由（50字以内）",
  "技能标签": ["标签1", "标签2", "标签3"]
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
            return result
            
        except Exception as e:
            raise ValueError(f"匹配度评估失败: {str(e)}")
    
    def process_resume(
        self,
        resume_base64: str,
        jd_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        完整的简历处理流程
        
        Args:
            resume_base64: Base64 编码的 PDF 简历
            jd_config: JD 配置
            
        Returns:
            完整的处理结果
        """
        # 1. 解析 PDF
        resume_text = self.parse_pdf_from_base64(resume_base64)
        
        # 2. 提取结构化信息
        structured_resume = self.extract_structure(resume_text)
        
        # 3. 评估匹配度
        evaluation = self.evaluate_match(structured_resume, jd_config)
        
        # 4. 组合结果
        result = {
            "structured_resume": structured_resume,
            "evaluation": evaluation,
            "raw_text_length": len(resume_text),
            "raw_resume_text": resume_text
        }
        
        return result

