#!/usr/bin/env python3
"""
LAMDA 顶级人才分析 - 使用 Planning-with-Files 模式
基于 Manus AI 的持久化 Markdown 规划模式
"""

import os

def create_planning_structure():
    """创建 3 文件规划结构"""

    # 1. 创建任务计划
    task_plan = """# Task Plan: LAMDA 顶级人才分析

## 目标
通过分析 LAMDA 实验室教授的顶级论文（NeurIPS/ICML/ICLR 等），识别最优秀的博士生和年轻研究者。

## 背景
- LAMDA 是南京大学机器学习实验室
- 周志华教授是创始人，Meta 收购的 Manus AI 使用类似的规划模式
- 需要从 251 名学生中识别真正的顶级人才

## 数据源
- LAMDA.xlsx: 原始学生数据
- LAMDA_profiles_zh_first_20260105_112233.xlsx: 爬取的成员信息
- Semantic Scholar API: 论文和引用数据
- Google Scholar: 备用查询

## Phases

- [x] Phase 1: 数据准备 ✓
  - [x] 爬取 LAMDA 成员信息 (253人)
  - [x] 提取联系方式 (181个邮箱)
  - [x] 识别核心导师 (6位，学生数≥20)
  - [x] 生成手动分析模板

- [ ] Phase 2: 论文数据分析 (当前阶段)
  - [ ] 测试 Semantic Scholar API 可行性
  - [ ] 为核心导师建立 Author ID 映射
  - [ ] 提取近5年顶级会议论文
  - [ ] 识别第一作者（通常是学生）

- [ ] Phase 3: 学生排名
  - [ ] 按顶级论文数排序
  - [ ] 按总引用数排序
  - [ ] 识别跨导师合作者
  - [ ] 标注学位状态（PhD/已毕业）

- [ ] Phase 4: 最终报告
  - [ ] 生成 Top 10 学生名单
  - [ ] 附带论文列表和引用统计
  - [ ] 提供联系方式
  - [ ] 给出推荐等级（高/中/低）

## Status
**Currently in Phase 2** - 测试 Semantic Scholar API

## Errors Encountered
- [x] Semantic Scholar 中文名搜索失败 → 解决：需要使用英文名
- [ ] API 限流 (429 errors) → 待解决：添加 API Key 或增加延迟
- [ ] Author ID 难以获取 → 待解决：手动收集或使用其他方法

## Key Insights
1. **中文名搜索问题**: "周志华" 会返回很多同名作者，但不是 LAMDA 的
2. **API 限制**: 免费 Semantic Scholar API 数据不完整
3. **手动验证最可靠**: 使用生成的模板 + Google Scholar 手动验证

## Next Steps
1. 为 6 位核心导师手动查找 Author ID
2. 或改用 Google Scholar + Selenium 自动化
3. 或使用手动分析模板（已生成）
"""

    # 2. 创建研究笔记
    notes = """# Research Notes: LAMDA 顶级人才分析

## Semantic Scholar API 测试

### 2025-01-05 13:00 - 初次测试
**尝试**: 搜索 "Zhi-Hua Zhou Nanjing University"
**结果**: 返回 94 个同名作者，但都不是 LAMDA 的周志华
**问题**: 中文名搜索不准确

**尝试**: 直接查询 Author ID
**结果**: 测试 ID 不对
**问题**: 不知道正确的 Author ID

### 发现
- Semantic Scholar API 免费版有限制
- 需要使用英文名字搜索
- 或者使用 Author ID 直接查询

### 核心导师名单
根据学生数量识别的核心导师：
1. 俞扬 (34名学生) - 强化学习、演化计算
2. 詹德川 (32名学生) - 机器学习理论、弱监督学习
3. 李宇峰 (26名学生) - 机器学习、度量学习
4. 章宗长 (22名学生)
5. 钱超 (21名学生)
6. 黎铭 (20名学生)
7. **周志华** (16名学生) - LAMDA 创始人，集成学习

### 关键发现
- 周志华虽然学生数不是最多，但是 LAMDA 创始人
- 爬虫已成功获取 181 个邮箱 (95.2% 覆盖率)
- 近5年博士生 60 人

## 手动分析方案
由于 API 限制，最佳方案是：
1. 使用生成的 Excel 模板
2. 对每个学生使用 Google Scholar 搜索
3. 手动统计顶级论文和引用

### 待解决的问题
- [ ] 如何获取教授的正确 Semantic Scholar Author ID？
- [ ] 是否值得申请付费 API Key？
- [ ] Selenium 自动化 Google Scholar 是否可行？
"""

    # 3. 创建最终输出框架
    deliverable = """# LAMDA 顶级人才分析报告

## 执行摘要
本报告通过分析 LAMDA 实验室 6 位核心导师的 60 名博士生，识别出最优秀的 AI 研究人才。

## 方法论
1. **数据来源**: LAMDA 官网、Semantic Scholar、Google Scholar
2. **分析时间**: 2025年1月
3. **评价标准**:
   - 顶级论文数（NeurIPS/ICML/ICLR/AAAI/IJCAI）
   - 总引用数
   - 第一作者论文数

## 核心发现

### Top 10 顶级学生
[待 Phase 3 完成]

### 按导师分类
[待 Phase 3 完成]

## 联系方式汇总
所有联系方式已在单独的 Excel 文件中提供。

## 推荐建议
[待 Phase 4 完成]

---

*报告生成时间: 2025-01-05*
*数据截止时间: 2024年12月*
"""

    # 创建目录
    os.makedirs('lamda_analysis_plan', exist_ok=True)

    # 写入文件
    with open('lamda_analysis_plan/task_plan.md', 'w', encoding='utf-8') as f:
        f.write(task_plan)

    with open('lamda_analysis_plan/notes.md', 'w', encoding='utf-8') as f:
        f.write(notes)

    with open('lamda_analysis_plan/final_report.md', 'w', encoding='utf-8') as f:
        f.write(deliverable)

    print("="*60)
    print("✓ Planning-with-Files 结构已创建")
    print("="*60)
    print("\n已创建以下文件:")
    print("  📋 lamda_analysis_plan/task_plan.md")
    print("  📝 lamda_analysis_plan/notes.md")
    print("  📄 lamda_analysis_plan/final_report.md")
    print("\n工作流程:")
    print("  1. 阅读 task_plan.md 了解目标")
    print("  2. 研究 → 更新 notes.md → 更新 task_plan.md")
    print("  3. 完成后更新 final_report.md")
    print("\n这就是 Manus AI 的工作模式！")
    print("="*60)

if __name__ == '__main__':
    create_planning_structure()
