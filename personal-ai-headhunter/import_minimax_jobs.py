#!/usr/bin/env python3
"""
Import MiniMax jobs from Feishu wiki pages into the headhunter database.
Source: https://vrfi1sk8a0.feishu.cn/wiki/GTxwwbvcFiJRcVkXESBc0yiyn5e
"""

import json
import os
from datetime import datetime

# Add project path to sys.path
import sys
sys.path.insert(0, '/Users/lillianliao/notion_rag/personal-ai-headhunter')

from database import SessionLocal, Job

# MiniMax job data scraped from Feishu Wiki
MINIMAX_JOBS = [
    # ========== B端业务 / Business Jobs ==========
    # Overseas Jobs
    {
        "title": "AI架构师 (AI Architect) - 海外",
        "company": "MiniMax",
        "department": "B端业务",
        "location": "美国, 日韩, 欧洲, 东南亚, 中东",
        "seniority_level": "一线 + senior",
        "raw_jd_text": """【岗位职责】
- 探索行业内新模型的玩法和落地场景
- 乐意对外和开发者交流

【岗位要求】
画像一：纯研发背景
1. 计算机专业
2. 性格外向，乐意对外和开发者交流
3. 有技术好奇心

画像二：有基础代码能力的SA
1. 有大模型相关项目实践
2. 有基本python能力
3. 英文可作为工作语言

【候选人画像】
- 优先华人，home base在目标区域
- 来源：头部云厂商（字节byteplus、华为云、agora、pingcap、腾讯云、阿里云海外）、AI初创公司等""",
        "hr_contact": "Sylvia (18186452676)",
        "urgency": 1,
        "headcount": 10,  # 海外AI架构师约10人
    },
    {
        "title": "Global Account Manager",
        "company": "MiniMax",
        "department": "B端业务",
        "location": "美国(SF), 欧洲(UK/德国/法国), 南美(墨西哥/巴西), 日韩, 中东(迪拜/阿联酋), 东南亚(泰国/马来/越南)",
        "seniority_level": "一线 + senior",
        "raw_jd_text": """【岗位职责】
- 负责海外市场的大客户销售工作

【岗位要求】
1. 优先华人，home base
2. 客户资源匹配：有泛互联网、游戏文娱、电商直播、广告媒体、web3、AI startup客户资源
3. 有云、AI/大模型产品销售经验
4. 销售能力突出：简历有明确quota和达成
5. 加分项：对AI有热情、状态aggressive

【推评估重点】
1. 客户资源集中的行业（列出2-3个代表客户）
2. 业绩（quota和达成情况）
3. 行业热情（对大模型行业认知、加入的意向度）

【目标公司】
1. AI/大模型公司 (Elevenlabs, Runway, Assemble, synthesia, heygen, deepgram, A21 labs, Mistral AI, Animaker AI, Abacus AI, Speechify, DeepBrain AI, Veed.io等视频生成/声音生成模型公司)
2. 头部云厂商（字节byteplus、华为云、agora、pingcap、腾讯云、阿里云海外、AWS、Google cloud、Azure等）""",
        "hr_contact": "Sylvia (18186452676)",
        "urgency": 1,
        "headcount": 20,  # 海外销售约20人
    },
    {
        "title": "Regional General Manager - 海外区域负责人",
        "company": "MiniMax",
        "department": "B端业务", 
        "location": "日韩, 欧洲, 中东",
        "seniority_level": "高级管理",
        "raw_jd_text": """【岗位职责】
区域业务负责人：
- 能判断大模型行业市场机会
- 孵化落地场景
- 制定海外销售策略

【岗位要求】
1. 有销售能力（背过明确的收入/增长等指标+拿到过结果）
2. 有0-1经历，对目标市场（欧洲/中东/日本）有insight
3. 对AI/大模型行业有认知和热情
4. 对创业公司有认知，有创业精神

【候选人画像】
优先中国人""",
        "hr_contact": "Sylvia (18186452676)",
        "urgency": 2,
        "headcount": 3,  # 区域负责人3人
    },
    # Domestic Jobs
    {
        "title": "大模型KA客户经理",
        "company": "MiniMax",
        "department": "B端业务",
        "location": "北京, 上海, 深圳, 广州, 香港",
        "seniority_level": "senior需3-1及以上",
        "raw_jd_text": """【工作地点】
- 北京：蓟门一号
- 上海：徐汇区新研大厦
- 深圳：南山区华润置地

【岗位职责】
一线销售：围绕销售目标做具体的落地执行，即战力强

【岗位要求】
1. 大KA sales：有千万级大客户项目运作经验，火山、阿里等云厂卖过tokens，理解业务逻辑，知道怎么打且卖出过业绩，能带来资源（优先看有泛互联网、游戏文娱、广告电商、AI startup行业客户资源的人）
2. 年轻高潜：年轻聪明、学习能力强、学过技术、有技术理解力、有冲劲（不要求客户资源和经验）
3. senior：过往扛过硬业务指标+拿到过结果，对大模型落地有全局认知，打法和客户思路清晰（每个节点的策略）

【目标公司】
1. 头部云厂：阿里云、字节火山、字节飞书、华为云、腾讯云、金山云、百度云、UCloud、pingcap、aws、azure、Google cloud
2. 大模型厂商：可灵、智谱、科大讯飞、Vidu""",
        "hr_contact": "Sylvia (18186452676)",
        "urgency": 2,
        "headcount": 15,  # 国内KA客户经理约15人
    },
    {
        "title": "AI架构师 (AI Architect) - 国内",
        "company": "MiniMax",
        "department": "B端业务",
        "location": "北京, 上海, 深圳, 广州, 香港",
        "seniority_level": "一线",
        "raw_jd_text": """【工作地点】
- 北京：蓟门一号
- 上海：徐汇区新研大厦
- 深圳：南山区华润置地

【岗位职责】
一线人员：探索行业内新模型的玩法和落地场景

【岗位要求】
画像一：纯研发背景
1. 计算机专业，前端/服务端/客户端背景
2. 接受转SA，不要求SA经验
3. 性格外向，乐意对外和开发者交流
4. 有技术好奇心

画像二：有基础代码能力的SA
1. 有大模型相关项目实践，有基本python能力
2. 英文可作为工作语言

【目标公司】
1. 头部云厂：阿里云、字节火山、字节飞书、华为云、腾讯云、UCloud、pingcap等
2. 大模型厂商：可灵、智谱、科大讯飞、Vidu
3. AI初创公司""",
        "hr_contact": "Sylvia (18186452676)",
        "urgency": 1,
        "headcount": 10,  # 国内AI架构师约10人
    },
    
    # ========== AI Infra / 计算平台 Jobs ==========
    {
        "title": "AI 推理框架工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7 (有一线能力的P8也可)",
        "raw_jd_text": """【岗位职责】
算子开发与推理框架优化

【岗位要求】
1. 算子开发：CUDA kernel、向量化访存、混合精度计算、通信算子（NCCL, RCCL）
2. 推理框架：高效 attention、speculative decoding、缓存复用、张量融合、DeepSpeed、FastTransformer

【目标公司】
1. 大厂大模型团队：字节 Seed/AML、阿里通义实验室/PAI/智能引擎、腾讯混元、快手
2. 大模型明星初创：DeepSeek、月之暗面、阶跃星辰、无问芯穹等""",
        "hr_contact": "达夫 (微信: Thinker)",
        "urgency": 2,
    },
    {
        "title": "训练框架研发工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7 (有一线能力的P8也可)",
        "raw_jd_text": """【岗位职责】
大规模分布式训练系统研发与性能极限优化

【岗位要求】
1. 大规模分布式训练系统研发：并行范式（FSDP/3D并行等）、高性能通信、集群利用率
2. 性能极限优化：训练吞吐优化、算子融合、精度压缩、通信调度、显存管理、量化、MoE、Speculative Training
3. 前沿训练技术探索：Agentic RL、异步 RL等机制的系统工程化落地
4. 与硬件深度协作：与底层 kernel / runtime / compiler 团队协作""",
        "hr_contact": "达夫 (微信: Thinker)",
        "urgency": 2,
    },
    {
        "title": "高性能服务研发工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7 (有一线能力的P8也可)",
        "raw_jd_text": """【岗位职责】
实时推理服务系统开发与优化

【岗位要求】
1. 服务架构开发：推理请求调度、负载均衡、动态批处理、请求切分/合并
2. 算法服务开发：在工程中做到"zero-overhead"，异步调度、缓存命中、KV cache 管理
3. 系统优化：GPU/CPU 协同、内存分配优化、网络通信优化
4. 热点问题探索：PD 分离、Large EP、多集群负载均衡、投机采样等""",
        "hr_contact": "达夫 (微信: Thinker)",
        "urgency": 2,
    },
    {
        "title": "模型服务化工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6+ ~ P7+",
        "raw_jd_text": """【岗位职责】
模型部署与业务稳定性框架开发

【岗位要求】
1. 业务稳定性经验：可观测、压测、容灾、调试、降级、灰度
2. 服务框架：流量入口、多云多机房
3. 模型部署经验

【目标公司】
传统公有云大厂&互联网大厂 infra 团队、明星初创、头部量化""",
        "hr_contact": "达夫",
        "urgency": 1,
    },
    {
        "title": "K8s 研发工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7 (有一线能力的P8也可)",
        "raw_jd_text": """【岗位职责】
云原生编排调度与容器化优化

【岗位要求】
1. 云原生：编排调度/资源优化/多云Fed/资源混布
2. Kubernetes/Volcano/Yarn
3. 容器化：docker/containerd""",
        "hr_contact": "达夫 (微信: Thinker)",
        "urgency": 1,
    },
    {
        "title": "大模型资源调度工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7",
        "raw_jd_text": """【岗位职责】
资源利用率优化与跨集群调度

【岗位要求】
1. ARH 资源调度：弹性调度、跨集群资源调度、负载均衡
2. ATM 离线资源：离线任务编排、离线任务调度、低优异构资源管理

【目标公司】
字节Scheduling、蚂蚁Scheduling、字节AML-Engine、阿里ACS、华为Volcano Yarn""",
        "hr_contact": "达夫 (微信: Thinker)",
        "urgency": 1,
    },
    {
        "title": "大模型流量调度工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7",
        "raw_jd_text": """【岗位职责】
高并发流量管理与服务治理

【岗位要求】
1. 负载均衡、service mesh、sidecar、Tracing、网络协议
2. 分布式组件（Redis/Etcd）、消息队列
3. 熟悉 Istio/Envoy/grpc/brpc/tracing""",
        "hr_contact": "达夫",
        "urgency": 1,
    },
    {
        "title": "AI Infra 平台研发工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7",
        "raw_jd_text": """【岗位职责】
PaaS 平台与算法工具开发

【岗位要求】
1. PaaS 平台开发经验
2. 算法平台及工具开发经验
3. 评测系统开发经验""",
        "hr_contact": "达夫 (微信: Thinker)",
        "urgency": 1,
    },
    {
        "title": "大模型数据链路工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7",
        "raw_jd_text": """【岗位职责】
高效大模型数据清洗与处理链路

【岗位要求】
1. 数据链路：大模型数据清洗/数据分类/数据采样
2. 熟悉数据引擎（Ray/Spark/Flink）
3. 熟悉数据湖与数据平台建设""",
        "hr_contact": "达夫",
        "urgency": 1,
    },
    {
        "title": "机器学习平台全栈工程师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P6 ~ P7",
        "raw_jd_text": """【岗位职责】
内部 AI 平台开发与前端交互

【岗位要求】
纯内部平台开发岗位，全栈偏前端的技术栈；有平台开发经验最好""",
        "hr_contact": "达夫",
        "urgency": 1,
    },
    {
        "title": "AI Infra 架构师",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "P7 ~ P8 (能在一线)",
        "raw_jd_text": """【岗位职责】
AI 基础设施架构设计与落地

【岗位要求】
在机器学习系统及泛 infra 岗位下，具有架构思维；能够在一线解决核心技术问题""",
        "hr_contact": "达夫",
        "urgency": 2,
    },
    {
        "title": "Top Infra (高潜/资深)",
        "company": "MiniMax",
        "department": "AI Infra / 计算平台",
        "location": "上海/北京",
        "seniority_level": "年轻高潜或者 7+ Senior",
        "raw_jd_text": """【岗位职责】
Infra 领域前沿探索与实践

【岗位要求】
1. 在 infra 的一个或多个领域有过深度实践或者探索
2. 对大模型有比较好的热爱和好奇心（两条都需要满足）""",
        "hr_contact": "达夫",
        "urgency": 2,
    },
]



def import_minimax_jobs():
    """Import MiniMax jobs into the database."""
    db = SessionLocal()
    
    try:
        # Get existing job titles for deduplication
        existing_titles = set(j.title for j in db.query(Job.title).all())
        print(f"📊 现有职位数: {len(existing_titles)}")
        
        # Find max M-prefix job code for MiniMax
        from sqlalchemy import text
        result = db.execute(text("SELECT MAX(CAST(SUBSTR(job_code, 2) AS INTEGER)) FROM jobs WHERE job_code LIKE 'M%'")).fetchone()
        max_code = result[0] if result[0] else 0
        
        imported = 0
        skipped = 0
        
        for job_data in MINIMAX_JOBS:
            title = job_data["title"]
            
            # Deduplication check
            if title in existing_titles:
                print(f"⏭️ 跳过 (已存在): {title}")
                skipped += 1
                continue
            
            # Generate job code
            max_code += 1
            job_code = f"M{max_code}"
            
            # Create job record
            job = Job(
                title=title,
                company=job_data.get("company", "MiniMax"),
                department=job_data.get("department"),
                location=job_data.get("location"),
                seniority_level=job_data.get("seniority_level"),
                raw_jd_text=job_data.get("raw_jd_text"),
                hr_contact=job_data.get("hr_contact"),
                urgency=job_data.get("urgency", 0),
                headcount=job_data.get("headcount"),  # 职位数量/HC
                job_code=job_code,
                jd_link="https://vrfi1sk8a0.feishu.cn/wiki/GTxwwbvcFiJRcVkXESBc0yiyn5e",
                detail_fields=json.dumps({
                    "source": "MiniMax Feishu Wiki",
                    "scraped_at": datetime.now().isoformat(),
                    "department": job_data.get("department"),
                    "seniority_level": job_data.get("seniority_level"),
                }, ensure_ascii=False),
                is_active=1,
            )
            
            db.add(job)
            existing_titles.add(title)
            imported += 1
            print(f"✅ 导入: [{job_code}] {title}")
        
        db.commit()
        
        print(f"\n{'='*50}")
        print(f"📊 导入统计:")
        print(f"   处理总数: {len(MINIMAX_JOBS)}")
        print(f"   跳过 (已存在): {skipped}")
        print(f"   新增导入: {imported}")
        print(f"{'='*50}")
        
        return imported, skipped
        
    except Exception as e:
        db.rollback()
        print(f"❌ 导入失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_minimax_jobs()
