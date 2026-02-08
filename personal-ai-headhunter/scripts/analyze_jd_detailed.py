#!/usr/bin/env python3
"""
算法JD详细分析脚本 - 细分大模型和多模态方向
"""
import sqlite3
import json
from collections import defaultdict

DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'

# 排除的非算法职位关键词
EXCLUDE_KEYWORDS = [
    '产品经理', '产品专家', '产品运营', '解决方案', '售前', '售后',
    '销售', '运营', '市场', 'HR', '招聘', '行政', '财务',
    '项目经理', 'PMO', '商务', '法务', '审计', '采购',
    '交付', '实施', '客户成功', '客服', '支持',
    '拓展', '增长运营', '在线销售', '负责人'
]

# 细分的分类体系
SUBCATEGORIES = {
    # 大模型细分
    'LLM-预训练/基座模型': ['预训练', 'Pre-train', '基座', '语言模型训练'],
    'LLM-对齐/RLHF': ['RLHF', '对齐', 'Alignment', '强化学习研发'],
    'LLM-Agent/智能体': ['Agent', '智能体', 'Function Call', 'Tool'],
    'LLM-RAG/知识库': ['RAG', '知识库', '检索增强', '向量'],
    'LLM-对话系统': ['对话', '交互', 'Chat', '问答'],
    'LLM-NLP通用': ['NLP', '自然语言', '文本'],
    
    # 多模态细分
    'MM-VLM/视觉语言': ['VLM', '视觉语言', 'Vision-Language', '多模态理解', '多模态'],
    'MM-图像生成/Diffusion': ['图像生成', 'Diffusion', '文生图', 'Text-to-Image', 'AIGC', '生成算法'],
    'MM-视频生成': ['视频生成', '视频编辑', 'Video'],
    'MM-3D/数字人': ['3D', '数字人', 'Avatar', '重建'],
    'MM-美颜/图像处理': ['美颜', '美型', '滤镜', '图像处理', '图像增强'],
    
    # CV细分
    'CV-目标检测/分割': ['检测', '分割', '识别', 'Detection', '视觉算法'],
    'CV-OCR/文字识别': ['OCR', '文字识别', '文档'],
    
    # 推荐/搜索/广告细分
    'RecSys-推荐算法': ['推荐'],
    'RecSys-搜索算法': ['搜索', '检索', '排序'],
    'RecSys-广告算法': ['广告', 'CTR', 'CVR', '投放', '出价'],
    
    # AI Infra细分
    'Infra-推理优化': ['推理', '加速', 'TensorRT', 'Inference'],
    'Infra-训练框架': ['训练', '分布式', 'DeepSpeed', 'Megatron'],
    'Infra-MLOps/平台': ['平台', 'MLOps', 'PAI', 'Pipeline'],
    'Infra-芯片/硬件': ['芯片', '硬件', 'FPGA', 'NPU'],
    
    # 其他
    'Audio-语音': ['语音', 'ASR', 'TTS', '音频', '音乐'],
    'Security-风控安全': ['风控', '安全', '反作弊'],
    'Embodied-具身智能': ['具身', '机器人', '运控', '导航', '仿真'],
}

def get_subcategory(title, jd_text):
    """获取细分类别"""
    text = (title + ' ' + (jd_text or ''))
    
    for subcat, keywords in SUBCATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                return subcat
    return 'Other-其他算法'

def is_algorithm_job(title):
    """判断是否是算法岗位"""
    # 排除非算法岗
    for kw in EXCLUDE_KEYWORDS:
        if kw in title:
            return False
    
    # 必须包含算法相关关键词
    algo_keywords = ['算法', '研究员', '科学家', '模型']
    
    for kw in algo_keywords:
        if kw in title:
            return True
    return False

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, job_code, title, company, location, required_experience_years, 
               notes, raw_jd_text
        FROM jobs 
        WHERE is_active = 1
    ''')
    jobs = cursor.fetchall()
    conn.close()
    
    # 分类所有JD
    all_algo_jobs = defaultdict(list)
    
    for job in jobs:
        job_id, job_code, title, company, location, exp_years, notes, jd_text = job
        
        if not is_algorithm_job(title):
            continue
        
        subcat = get_subcategory(title, jd_text or '')
        
        # 解析紧急度
        urgency = ''
        if notes:
            if '五星' in notes or '最高' in notes or '紧急度很高' in notes:
                urgency = '🔥P0'
            elif '三星' in notes or '紧急' in notes or '纯急' in notes:
                urgency = '⚡P1'
        
        all_algo_jobs[subcat].append({
            'job_code': job_code or '-',
            'title': title,
            'company': company,
            'urgency': urgency
        })
    
    # 输出结果
    print('=' * 90)
    print('📊 算法 JD 完整清单 (按细分类别)')
    print('=' * 90)
    
    # 按类别排序
    category_order = [
        'LLM-预训练/基座模型', 'LLM-对齐/RLHF', 'LLM-Agent/智能体', 
        'LLM-RAG/知识库', 'LLM-对话系统', 'LLM-NLP通用',
        'MM-VLM/视觉语言', 'MM-图像生成/Diffusion', 'MM-视频生成', 
        'MM-3D/数字人', 'MM-美颜/图像处理',
        'CV-目标检测/分割', 'CV-OCR/文字识别',
        'RecSys-推荐算法', 'RecSys-搜索算法', 'RecSys-广告算法',
        'Infra-推理优化', 'Infra-训练框架', 'Infra-MLOps/平台', 'Infra-芯片/硬件',
        'Audio-语音', 'Security-风控安全', 'Embodied-具身智能', 'Other-其他算法'
    ]
    
    total_count = 0
    summary = []
    
    for cat in category_order:
        jobs_in_cat = all_algo_jobs.get(cat, [])
        if not jobs_in_cat:
            continue
        
        total_count += len(jobs_in_cat)
        urgent_count = len([j for j in jobs_in_cat if j['urgency']])
        summary.append((cat, len(jobs_in_cat), urgent_count))
        
        print(f'\n{"="*90}')
        print(f'📁 {cat} ({len(jobs_in_cat)}个{", " + str(urgent_count) + "个紧急" if urgent_count else ""})')
        print(f'{"="*90}')
        print(f'{"编号":<12} {"职位名称":<45} {"公司":<18} {"紧急":<6}')
        print('-' * 90)
        
        # 按紧急度排序
        jobs_sorted = sorted(jobs_in_cat, key=lambda x: (x['urgency'] == '', x['job_code']))
        
        for job in jobs_sorted:
            title_short = job['title'][:43] if len(job['title']) > 43 else job['title']
            company_short = job['company'][:16] if len(job['company']) > 16 else job['company']
            print(f'{job["job_code"]:<12} {title_short:<45} {company_short:<18} {job["urgency"]:<6}')
    
    print(f'\n{"="*90}')
    print(f'📊 总计: {total_count} 个算法岗位')
    print(f'{"="*90}')
    
    # 统计汇总
    print('\n📈 分类统计汇总:')
    print('-' * 60)
    for cat, count, urgent in summary:
        bar = '█' * (count // 2) if count >= 2 else '▪'
        urgent_mark = f' 🔥({urgent}个紧急)' if urgent > 0 else ''
        print(f'{cat:<28} {bar:<20} {count:>3}个{urgent_mark}')

if __name__ == '__main__':
    main()
