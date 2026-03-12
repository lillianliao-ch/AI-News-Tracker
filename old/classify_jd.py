"""
JD 分类打标脚本
根据具身智能/机器人行业的岗位分类标准，对岗位进行自动标签
"""
import pandas as pd
import re
from typing import Tuple, List

# ========== 分类规则定义 ==========

# L1 系统与整机层 - 对整机系统架构、平台能力、最终性能负责
L1_KEYWORDS = [
    '系统架构', '系统工程', '整机', '本体', '架构师', '平台负责人',
    '硬件系统', '域控制器', '端侧系统', '系统集成', 'AI 系统架构',
    '系统产品规划', '软件架构师', '系统产品经理', '产品线技术 Leader',
    '机器人系统产品'  
]

# L2 控制与动力学 - 对机器人"能不能稳、准、强地动"负责
L2_KEYWORDS = [
    '运动控制', '运控', '规控', 'MPC', 'WBC', '力控', 
    '足式', '全身控制', '控制算法', '运控器件',
    '仿真', '动力学', '机器人控制'
]

# L3 机器人智能算法 - 对"感知 / 决策 / 学习能力"负责
L3_CORE_ROBOTICS_KEYWORDS = [
    'SLAM', 'VSLAM', '感知', '3D 视觉', '三维视觉', '规控算法',
    '强化学习', 'RL', '数据闭环', '机器人算法', '运筹算法', '运筹优化',
    '算法工程师', '算法专家', '仓储机器人调度', '调度算法'
]
L3_NARRATIVE_AI_KEYWORDS = [
    '大模型', '多模态', 'VLA', '动作大模型', 'AIGC', '推理加速',
    'LLM', 'GPT', 'AI 算法', 'AI 开发'
]

# L4 系统软件与工具链 - 对"工程化、平台化、效率与稳定性"负责
L4_KEYWORDS = [
    'C++', 'Golang', 'Go 开发', '嵌入式', 'MCU', 'BSP', 
    'ROS', '中间件', '仿真平台', '数据平台', '工具链',
    'Java', '后端', '前端', '软件开发', '开发工程师', '高级开发',
    '测试工程师', '软件测试', '自动化测试', '测试开发',
    'DBA', '运维', '数据库', '研发效能', '集成测试',
    '大数据', '数据工程师', '云运维', 'WMS', 'WES'
]

# L5 产品化与交付 - 对"技术 → 产品 → 客户价值"负责
L5_KEYWORDS = [
    '产品经理', '产品专家', '项目经理', 'TPM', 'PMO',
    '解决方案', '售前', 'FAE', '现场应用', '交付', '实施',
    '软件顾问', '技术支持', '售后', '客户成功',
    '交付项目经理', '实施工程师', '交付工程师', '交付顾问'
]

# L6 商业与组织支撑 - 非技术核心
L6_KEYWORDS = [
    'HR', 'HRBP', '招聘', '人事', '人力资源', '人才发展', '培训',
    '财务', '法务', '合规', '销售', '市场', 'KA', '大客户',
    '行政', '仓储', '采购', '供应', '物料', '生产', '制造',
    '质量', 'SQE', 'PQA', '安全员', 'EHS', '投资者关系',
    '普工', '操作工', '钳工', '电工', '绘图', 'CAD', '工段长',
    '成本', 'BOM', '文员', '统筹'
]

# ========== 二级标签规则 ==========

def get_secondary_tags(job_title: str) -> List[str]:
    """获取二级标签"""
    tags = []
    title_lower = job_title.lower()
    
    # Tag 1: Intern / External
    if '实习' in job_title or '实习生' in job_title:
        tags.append('Intern')
    if '外包' in job_title or '派遣' in job_title:
        tags.append('External')
    
    # Tag 2: Client-Side
    if any(kw in job_title for kw in ['前端', 'Flutter', 'UI', 'UX', '客户端', 'ID 设计']):
        tags.append('Client-Side')
    
    # Tag 3: Data / Platform
    if any(kw in job_title for kw in ['数据', '数据平台', '数据中台', '大数据', 'DBA']):
        tags.append('Data')
    
    # Tag 4: Core-Robotics vs Narrative-AI (算法岗位)
    if any(kw in job_title for kw in L3_CORE_ROBOTICS_KEYWORDS):
        tags.append('Core-Robotics')
    if any(kw in job_title for kw in L3_NARRATIVE_AI_KEYWORDS):
        tags.append('Narrative-AI')
    
    # Tag 5: Scene (场景)
    if any(kw in job_title for kw in ['物流', '仓储', '仓库', 'WMS', 'WES']):
        tags.append('Logistics')
    if any(kw in job_title for kw in ['工业', '制造', '产线']):
        tags.append('Industrial')
    if any(kw in job_title for kw in ['教育', '培训']):
        tags.append('Education')
    if any(kw in job_title for kw in ['消费', '家用', '服务']):
        tags.append('Consumer')
    
    # 额外标签
    if any(kw in job_title for kw in ['机器人', '本体', '整机']):
        tags.append('Robotics')
    if '硬件' in job_title:
        tags.append('Hardware')
    if '电气' in job_title or '电工' in job_title:
        tags.append('Electrical')
    if '机械' in job_title or '结构' in job_title:
        tags.append('Mechanical')
    if '海外' in job_title or '英文' in job_title or '外企' in job_title:
        tags.append('International')
    if '校招' in job_title or '届' in job_title:
        tags.append('Campus')
    
    return tags

def classify_job(job_title: str) -> Tuple[str, str, List[str]]:
    """
    对岗位进行分类
    返回: (Level, Level名称, 二级标签列表)
    """
    title = job_title.strip()
    
    # 优先级判断（从最具体到最通用）
    
    # 首先检查是否是 L6 商业/组织/支撑岗位
    l6_patterns = [
        '招聘', 'HR', 'HRBP', '人事', '人力资源', '人才发展', '培训专家',
        '销售', 'KA', '大客户', '市场',
        '财务', '法务', '合规', '投资者关系',
        '行政', '普工', '操作工', '钳工', '电工', '工段长', '文员',
        '采购', '供应', '物料计划', '生产', '制造代表', '生产安全', '安全员',
        'EHS', '跟单', '订单', 'BOM', '备品备件', '质量体系', 
        'SQE', 'PQA', '成本工程师', 'CNC', '绘图', 'CAD',
        '认证工程师', '服务类供应商', '制造代表', 'ID 设计', '机械 Leader',
        '临时对话'
    ]
    for pattern in l6_patterns:
        if pattern in title:
            return 'L6', '商业与组织支撑', get_secondary_tags(title)
    
    # L4 优先：测试架构师、软件测试专家等仍归 L4（不是 L1 架构师）
    l4_early_patterns = [
        '软件测试架构', '测试架构师', '测试技术'
    ]
    for pattern in l4_early_patterns:
        if pattern in title:
            return 'L4', '系统软件与工具链', get_secondary_tags(title)
    
    # L1 系统与整机层（必须是系统架构 / AI 系统 / 机器人系统级别）
    l1_patterns = [
        'AI 系统架构', '机器人系统产品', '系统架构师', 
        '整机', '本体研发', '产品线技术 Leader'
    ]
    for pattern in l1_patterns:
        if pattern in title:
            return 'L1', '系统与整机层', get_secondary_tags(title)
    
    # 架构师 - 需要细分（软件架构师属于 L4，系统架构师属于 L1）
    if '架构师' in title:
        if '软件架构' in title or 'Java' in title:
            return 'L4', '系统软件与工具链', get_secondary_tags(title)
        else:
            return 'L1', '系统与整机层', get_secondary_tags(title)
    
    # L5 产品规划类（优先于 L1，因为更偏产品化）
    l5_planning_patterns = [
        '系统产品规划', '流通系统产品规划', '系统产品经理'
    ]
    for pattern in l5_planning_patterns:
        if pattern in title:
            return 'L5', '产品化与交付', get_secondary_tags(title)
    
    # L2 控制与动力学
    l2_patterns = [
        '运动控制', '运控', '规控', 'MPC', 'WBC', '力控',
        '足式', '全身控制', '控制算法', '仿真工程', '仿真应用',
        '机器人控制', '动力学'
    ]
    for pattern in l2_patterns:
        if pattern in title:
            return 'L2', '控制与动力学', get_secondary_tags(title)
    
    # 运控器件系统工程师 - 属于 L4（硬件系统组件）
    if '运控器件' in title:
        return 'L4', '系统软件与工具链', get_secondary_tags(title)
    
    # 仿真岗位的判断（可能是 L2 或 L5）
    if '仿真产品' in title:
        return 'L5', '产品化与交付', get_secondary_tags(title)
    if '仿真' in title:
        return 'L2', '控制与动力学', get_secondary_tags(title)
    
    # L3 机器人智能算法
    l3_core_patterns = [
        'SLAM', 'VSLAM', '感知', '3D 视觉', '三维视觉',
        '强化学习', 'RL', '运筹算法', '运筹优化', '调度算法',
        '算法专家', '算法工程师', '算法研究员'
    ]
    for pattern in l3_core_patterns:
        if pattern in title:
            return 'L3', '机器人智能算法', get_secondary_tags(title)
    
    l3_narrative_patterns = ['大模型', '多模态', 'VLA', 'LLM', 'AIGC']
    for pattern in l3_narrative_patterns:
        if pattern in title:
            return 'L3', '机器人智能算法', get_secondary_tags(title)
    
    # L5 产品化与交付（优先于 L4，因为产品/交付岗位更明确）
    l5_patterns = [
        '产品经理', '产品专家', '高级产品', '项目经理', 'TPM', 'PMO',
        '解决方案', '售前', 'FAE', '现场应用', '交付', '实施',
        '软件顾问', '技术支持', '售后', '产品管理', '产品规划',
        '软件实施', '交付顾问', '功能安全专家'
    ]
    for pattern in l5_patterns:
        if pattern in title:
            return 'L5', '产品化与交付', get_secondary_tags(title)
    
    # L4 系统软件与工具链
    l4_patterns = [
        'Java', 'Golang', 'Go 开发', '后端', '前端', '开发工程师',
        '嵌入式', 'MCU', 'BSP', 'ROS', '中间件',
        '测试工程师', '软件测试', '自动化测试', '测试开发', '测试专家',
        '测试架构', '集成测试', '算法测试',
        'DBA', '运维', '大数据', '数据工程', '数据平台',
        '研发效能', '硬件测试', '本体测试', '机器人测试',
        '电气工程师', '机械工程师', '电气技术', '硬件产品测试'
    ]
    for pattern in l4_patterns:
        if pattern in title:
            return 'L4', '系统软件与工具链', get_secondary_tags(title)
    
    # 备用匹配 - 通用关键词
    if '软件' in title and '产品' not in title:
        return 'L4', '系统软件与工具链', get_secondary_tags(title)
    
    if '工程师' in title:
        return 'L4', '系统软件与工具链', get_secondary_tags(title)
    
    if '产品' in title:
        return 'L5', '产品化与交付', get_secondary_tags(title)
    
    # 默认归类
    return 'L6', '商业与组织支撑', get_secondary_tags(title)

def main():
    # 读取 Excel 文件
    input_file = '具身智能招聘岗位list.xlsx'
    output_file = '具身智能招聘岗位list_已分类.xlsx'
    
    print(f"正在读取 {input_file}...")
    df = pd.read_excel(input_file)
    
    print(f"共 {len(df)} 条记录，开始分类...")
    
    # 对每个岗位进行分类
    results = []
    for idx, row in df.iterrows():
        job_title = row['职位名称']
        level, level_name, tags = classify_job(job_title)
        results.append({
            'Level': level,
            'Level名称': level_name,
            '二级标签': ', '.join(tags) if tags else ''
        })
    
    # 添加分类结果到 DataFrame
    result_df = pd.DataFrame(results)
    df['一级分类(Level)'] = result_df['Level']
    df['一级分类名称'] = result_df['Level名称']
    df['二级标签'] = result_df['二级标签']
    
    # 重新排列列顺序
    cols = list(df.columns)
    # 把分类列放到前面
    new_cols = ['序号', '职位名称', '一级分类(Level)', '一级分类名称', '二级标签'] + \
               [c for c in cols if c not in ['序号', '职位名称', '一级分类(Level)', '一级分类名称', '二级标签']]
    df = df[new_cols]
    
    # 保存结果
    df.to_excel(output_file, index=False)
    print(f"分类完成！结果已保存到 {output_file}")
    
    # 打印统计信息
    print("\n========== 分类统计 ==========")
    level_counts = df['一级分类(Level)'].value_counts().sort_index()
    for level, count in level_counts.items():
        level_name = df[df['一级分类(Level)'] == level]['一级分类名称'].iloc[0]
        print(f"{level} ({level_name}): {count} 个岗位")
    
    print("\n========== 各分类示例 ==========")
    for level in ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']:
        subset = df[df['一级分类(Level)'] == level]
        if len(subset) > 0:
            level_name = subset['一级分类名称'].iloc[0]
            print(f"\n{level} | {level_name}:")
            for _, row in subset.head(5).iterrows():
                tags = row['二级标签']
                tag_str = f" [{tags}]" if tags else ""
                print(f"  - {row['职位名称']}{tag_str}")

if __name__ == '__main__':
    main()
