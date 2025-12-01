import pandas as pd

data = [
    {
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "current_company": "Tech Corp",
        "current_title": "Python Backend Engineer",
        "education": "本科",
        "experience": "5年",
        "resume_text": "资深 Python 后端工程师，熟悉 Django/Flask，有 5 年高并发系统开发经验。熟悉 MySQL, Redis, Docker。曾在 Tech Corp 负责支付网关开发。"
    },
    {
        "name": "李四",
        "email": "lisi@example.com",
        "phone": "13900139000", 
        "current_company": "AI Lab",
        "current_title": "Data Scientist",
        "education": "硕士",
        "experience": "3年",
        "resume_text": "数据科学家，专注于 NLP 领域。熟练使用 PyTorch, TensorFlow, HuggingFace。有 RAG 系统搭建经验。熟悉大模型微调。"
    },
     {
        "name": "王五",
        "email": "wangwu@example.com",
        "phone": "13700137000",
        "current_company": "Mobile Soft",
        "current_title": "Product Manager",
        "education": "本科",
        "experience": "6年",
        "resume_text": "6年互联网产品经验，主要负责 B 端 SaaS 产品。擅长需求分析、原型设计（Axure/Figma）。有极强的沟通协调能力。"
    }
]

df = pd.DataFrame(data)
try:
    # 优先尝试 .xlsx
    df.to_excel("personal-ai-headhunter/sample_candidates.xlsx", index=False)
    print("Sample data created: sample_candidates.xlsx")
except Exception as e:
    print(f"Excel write failed: {e}. Falling back to CSV.")
    df.to_csv("personal-ai-headhunter/sample_candidates.csv", index=False)
    print("Sample data created: sample_candidates.csv")
