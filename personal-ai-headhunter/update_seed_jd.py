#!/usr/bin/env python3
"""
批量更新Seed Application职位JD内容到数据库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Job

# Seed Application 职位数据
JD_DATA = [
    {
        "db_id": 817,
        "title": "AIGC模型应用算法工程师/专家-Seed",
        "job_code": "A120348",
        "location": "北京",
        "jd_content": """【职位描述】
1、负责AIGC基础模型相关技术的研究和开发，优化豆包AI创作效果，包括图像模型、Agent模型等；
2、向字节跳动内部产品提供基础模型及相关应用的支持；
3、探索以大模型能力为核心的AI创作新产品。

【职位要求】
1、1-5年计算机视觉一个或多个领域的研究和实践经验，包括但不限于以下方向：
1）图像生成/编辑、视频生成/编辑；
2）生成、理解模型的大规模训练；
3）VLM的Post-Training（SFT、RM & RL）；
4）多模态数据生产或多模态模型评测；
5）生成模型的蒸馏等；
2、动手能力强，熟练的编程能力，熟悉C++和Python编程；
3、对AI技术的实际落地和突破性应用充满热情，追求技术创新与现实价值的结合；
4、良好的自驱力，思维敏捷，追求本质，敢于挑战未知问题；
5、在CVPR/NeurIPS/ICCV/ICLR等顶级会议上发表论文者优先；有数学、编程竞赛经验者有加分。"""
    },
    {
        "db_id": 818,
        "title": "AIGC视频生成算法工程师-火山方舟",
        "job_code": "A26396",
        "location": "北京",
        "jd_content": """【职位描述】
1、优化Seedance系列模型，为模型的通用能力提升相关技术负责，同时重点关注模型在影视、动漫、广告、营销等生产力场景的效果；
2、解决生成视频生成中的一致性、运动质量、稳定性等核心研究难题；
3、紧跟生成方向的最新研究动态（理解生成统一、超长视频生成、流式互动视频生成等），并对创新想法进行原型验证。

【职位要求】
1、在多模态、AIGC等一个或多个领域有较深入的研究者，熟悉生成相关技术路线（扩散模型，自回归模型等），有大规模训练经验、AIGC、VLM、音视频生成等相关经验；
2、动手能力强，具有熟练的算法和编程能力，熟悉C/C++和Python编程；
3、工作积极主动，能与团队融洽合作相处，同时能够独立完成研究工作；
4、在CVPR、ECCV、ICCV、NeurIPS、ICLR、SIGGRAPH等顶级会议/期刊上发表论文者优先。"""
    },
    {
        "db_id": 819,
        "title": "AIGC图像生成算法工程师-火山方舟",
        "job_code": "A34626A",
        "location": "北京",
        "jd_content": """【职位描述】
1、优化Seedream系列模型，为模型的通用能力提升相关技术负责，包含图像理解、图像生成、图像编辑等前沿技术；
2、推动技术在内容创作/特效/素材生成/辅助设计等领域的应用；
3、参与技术规划制定，把握图像生成技术最新发展趋势。

【职位要求】
1、在多模态、AIGC等一个或多个领域有较深入的研究者，熟悉生成相关技术路线（扩散模型，自回归模型等），有大规模训练经验、AIGC、VLM、音视频生成等相关经验；
2、动手能力强，具有熟练的算法和编程能力，熟悉C/C++和Python编程；
3、工作积极主动，能与团队融洽合作相处，同时能够独立完成研究工作；
4、在CVPR、ECCV、ICCV、NeurIPS、ICLR、SIGGRAPH等顶级会议/期刊上发表论文者优先。"""
    },
    {
        "db_id": 820,
        "title": "大模型算法工程师（语音）-火山方舟",
        "job_code": "A40260",
        "location": "北京",
        "jd_content": """【职位描述】
1、参与研发多模态模型等下一代人工智能核心技术；
2、关注和推进技术在业务场景中的广泛应用，包括但不限于语言、音乐、语音、音频的生成与多模态理解等；
3、深入调研和关注音频/NLP/多模态等方向的前沿技术。

【职位要求】
1、计算机科学/计算机工程/电子信息技术等相关专业优先，3年以上算法工作经验；
2、有自然语言处理、语音合成与识别、音乐生成等研究或者技术背景优先；
3、有预训练技术，包括但不限于高效训练、强化学习，参与过研发音频、NLP相关的预训练模型及其下游应用者优先；
4、优秀的代码能力、数据结构和基础算法功底，C/C++或Python熟练；
5、有领域顶级会议文章（NeurIPS、ICML、ICLR、CVPR、ICCV、ACL、KDD等）优先；
6、熟悉大模型相关前沿方向（SeedTTS、CosyVoice、Qwen-omni、Veo3），在相关领域有过良好研究记录者优先。"""
    },
    {
        "db_id": 821,
        "title": "豆包大模型算法工程师（互动娱乐）-火山方舟",
        "job_code": "A236465",
        "location": "北京",
        "jd_content": """【职位描述】
1、负责参与Character-LLM迭代优化，包括但不限于数据合成、数据筛选、数据分析、Posttraining等任务；
2、负责参与游戏Agent和CodeAgent任务的设计，环境的构建、Reward的设计以及保障RL的正确训练；
3、负责语音S2S在通用任务上基础能力的优化，支持类似FC、RAG等场景；负责语音S2S在角色扮演及真人对话上拟人能力的提升；
4、对RM、RL、Agent有技术探索的热情。

【职位要求】
1、计算机相关专业本科及以上学历，一年及以上大模型算法工作经验；
2、有RL训练经验，熟悉如GRPO、PPO、DAPO，有较强的RL分析和改进经验；
3、优秀的代码能力、数据结构和基础算法功底，C/C++或Python熟练；
4、有领域顶级会议文章（NeurIPS、ICML、ICLR、CVPR、ICCV、ACL、KDD等）优先；
5、熟悉大模型相关的算法和技术，在相关领域有过良好研究记录者优先；
6、在大模型领域，主导参与过大影响力的项目或论文者优先。"""
    },
]


def main():
    db = SessionLocal()
    
    updated = 0
    
    for job_data in JD_DATA:
        job = db.query(Job).filter(Job.id == job_data["db_id"]).first()
        if job:
            job.title = job_data["title"]
            job.job_code = job_data["job_code"]
            job.location = job_data["location"]
            job.raw_jd_text = job_data["jd_content"]
            print(f"✅ 更新: {job_data['title']} ({job_data['job_code']})")
            updated += 1
    
    db.commit()
    print(f"\n📊 完成: 更新 {updated} 个 Seed Application 职位")


if __name__ == "__main__":
    main()
