---
title: "LAMDA 学生深度挖掘和评估系统 - 行动计划"
created: "2025-01-27"
status: "active"
version: "1.0"
author: "Claude + Lillian"
project: "LAMDA Scraper Enhancement"
target: "南大学生深度挖掘和综合评分系统"

mission: |
  从南京大学学生列表中，深度挖掘候选人的研究信息（方向、论文、GitHub、LinkedIn、邮箱等），
  建立综合评分体系，自动分层分类（Tier A/B/C），生成高质量候选人数据库，
  最终实现智能推荐和精准匹配。

current_status:
  phase: "Phase 1 完成 - 数据增强"
  completed_tasks:
    - GitHub URL 标准化 (98.9% 正确率)
    - Cloudflare 邮箱解码
    - 重定向跟随 (HTTP + meta refresh + JavaScript)
    - 批量邮箱提取 (+15个邮箱)
  ongoing_tasks:
    - 优先级邮箱提取（运行中）
  next_phase: "Phase 2 - 深度信息提取"

goals:
  primary:
    - 建立完整的南大学生画像数据库
    - 实现多维度综合评分系统
    - 自动分层分类 (Tier A/B/C)
    - 生成可执行的候选人推荐列表

  secondary:
    - 提取完整研究信息（论文、方向）
    - 整合多源数据（GitHub Scholar、GitHub、LinkedIn）
    - 建立智能匹配和推荐系统

  metrics:
    - 数据完整性: 从 60% → 85%+
    - 评分覆盖率: 从 0% → 100%
    - 处理效率: 提升 3-5 倍
    - Tier A 候选人: 识别出前 10%

tasks:
  - id: "P1-001"
    title: "实现深度信息提取器"
    priority: "P0"
    status: "pending"
    estimate: "1-2天"
    dependencies: []

    description: |
      创建深度爬虫，从南大学生个人主页提取完整信息：
      1. 基本信息（姓名、导师、入学年份）
      2. 研究方向（从个人主页/论文摘要提取）
      3. 社交媒体链接（GitHub、Google Scholar、LinkedIn）
      4. 联系方式（邮箱、优先级排序）

    output:
      - "deep_student_scraper.py"
      - 提取 10 个样本学生数据

    acceptance_criteria:
      - 成功提取研究方向（准确率 > 80%）
      - 成功提取 Google Scholar 链接（覆盖率 > 60%）
      - 成功提取 GitHub 链接（覆盖率 > 50%）

    implementation_details: |
      使用 BeautifulSoup + requests：
      1. 解析个人主页 HTML
      2. 识别关键 section（研究兴趣、论文列表）
      3. 提取外部链接（Scholar、GitHub、LinkedIn）
      4. 邮箱提取（明文 + Cloudflare 解码）

    notes: |
      参考 enhanced_website_scraper.py 的实现
      添加重定向跟随（已有 redirect_utils.py）

  - id: "P1-002"
    title: "Google Scholar 提取器"
    priority: "P0"
    status: "pending"
    estimate: "1天"
    dependencies: []

    description: |
      创建 Google Scholar 提取器，获取学生的论文信息：
      1. 从 Scholar 个人主页提取论文列表
      2. 识别论文质量（venue 类型、引用数）
      3. 判断 CCF 分级（A/B/C 类）
      4. 提取第一作者论文

    output:
      - "google_scholar_extractor.py"
      - 提取 10 个样本的论文数据

    acceptance_criteria:
      - 成功提取论文标题（准确率 > 95%）
      - 成功识别 venue 类型（NeurIPS/ICML 等）
      - 正确判断 CCF 分级（准确率 > 90%）

    implementation_details: |
      使用 BeautifulSoup 或 Scholar API：
      1. 解析 Scholar HTML 结构
      2. 提取论文元数据（标题、作者、年份、venue）
      3. venue 类型映射（NeurIPS → CCF-A）
      4. 引用数提取

    notes: |
      注意 Scholar 的速率限制
      可以用第三方库（scholarly）作为备选

  - id: "P1-003"
    title: "GitHub 深度分析器"
    priority: "P0"
    status: "pending"
    estimate: "1天"
    dependencies: []

    description: |
      增强 GitHub 分析能力，评估技术实力：
      1. 提取所有仓库信息
      2. 计算 stars/forks 分布
      3. 分析技术栈（语言、topics）
      4. 评估项目质量（核心指标）

    output:
      - "github_deep_analyzer.py"
      - 分析 10 个样本的 GitHub 数据

    acceptance_criteria:
      - 成功提取所有仓库
      - 准确计算技术栈
      - 质量评分与人工评估一致

    implementation_details: |
      基于 github_email_enricher.py 扩展：
      1. 获取用户的所有 repos
      2. 统计 stars/forks/commits
      3. 提取 languages 和 topics
      4. 识别核心项目（stars > 100）

    notes: |
      已有 GitHub Token 管理
      注意 API 速率限制（5000次/小时）

  - id: "P2-001"
    title: "综合评分系统"
    priority: "P1"
    status: "pending"
    estimate: "2-3天"
    dependencies: ["P1-001", "P1-002", "P1-003"]

    description: |
      实现多维度综合评分系统（参考 GitHub Miner）：
      1. 学术能力（30分）- 论文、h-index、引用
      2. 技术能力（25分）- GitHub、项目、技术栈
      3. 实践经验（20分）- 实习、项目、工作
      4. 可联系性（15分）- 邮箱、LinkedIn、网站
      5. 发展潜力（10分）- 导师、研究方向热度

    output:
      - "comprehensive_scorer.py"
      - 462 个候选人全部评分

    acceptance_criteria:
      - 100% 覆盖率
      - Tier A/B/C 分层合理
      - 与人工评估一致性 > 80%

    implementation_details: |
      参考 github_network_miner.py 的评分逻辑：
      1. 定义评分维度和权重
      2. 实现信号提取
      3. 计算综合分数
      4. 确定分层等级

    评分权重：
      学术: 0.3, 技术: 0.25, 经验: 0.2, 联系: 0.15, 潜力: 0.1

    notes: |
      这是整个系统的核心！
      需要多次调试和校准
      先用 10 个样本测试

  - id: "P2-002"
    title: "LinkedIn 提取器（可选）"
    priority: "P2"
    status: "pending"
    estimate: "2-3天"
    dependencies: []

    description: |
      创建 LinkedIn 提取器，获取职业经历：
      1. 从个人主页找到 LinkedIn 链接
      2. 提取工作经历（公司、职位、时间）
      3. 识别大厂实习（字节、腾讯、微软等）

    output:
      - "linkedin_extractor.py"
      - 提取 20 个样本的职业数据

    acceptance_criteria:
      - 成功提取工作经历
      - 准确识别大厂实习

    implementation_details: |
      LinkedIn 难度较大，方案：
      方案A: 使用 LinkedIn API（需要申请）
      方案B: 使用 Selenium 爬取（简单但可能被检测）
      方案C: 手动补充（可控制质量）

    notes: |
      如果 LinkedIn 太难，可以降低优先级
      职业经历可以从简历等其他渠道获取

  - id: "P2-003"
    title: "智能速率限制管理器"
    priority: "P1"
    status: "pending"
    estimate: "0.5天"
    dependencies: []

    description: |
      实现智能速率限制管理（参考 GitHub Miner）：
      1. 检测 403 错误
      2. 指数退避重试（10s → 20s → 40s → 80s → 160s）
      3. 随机抖动（避免请求模式）
      4. 动态延迟调整

    output:
      - "smart_rate_limiter.py"
      - 整合到所有爬虫

    acceptance_criteria:
      - API 调用成功率 > 95%
      - 效率提升 3-5 倍

    implementation_details: |
      参考 github_network_miner.py 的 _request 方法

    notes: |
      这是提升效率的关键！
      可以立即实施，影响所有后续任务

  - id: "P3-001"
    title: "分阶段处理流水线"
    priority: "P2"
    status: "pending"
    estimate: "1天"
    dependencies: ["P2-001"]

    description: |
      重构为清晰的分阶段处理流程：
      Phase 1: 数据采集和基础清洗
      Phase 2: 深度信息提取
      Phase 3: 综合评分和分类
      Phase 4: 验证和报告

    output:
      - "lamda_pipeline.py"
      - 每阶段可独立执行和验证

    acceptance_criteria:
      - 每阶段可独立运行
      - 每阶段有验证函数
      - 支持断点续处理

    implementation_details: |
      参考 github_network_miner.py 的命令行接口：
      python lamda_pipeline.py phase1
      python lamda_pipeline.py verify1
      python lamda_pipeline.py phase2
      ...

    notes: |
      改善流程可维护性
      便于调试和验证

  - id: "P3-002"
    title: "数据质量监控系统"
    priority: "P2"
    status: "pending"
    estimate: "1天"
    dependencies: ["P3-001"]

    description: |
      创建数据质量监控和验证系统：
      1. 字段完整性检查
      2. 数据质量评分
      3. 异常数据检测
      4. 生成验证报告

    output:
      - "data_quality_monitor.py"
      - 每阶段生成验证报告

    acceptance_criteria:
      - 实时质量监控
      - 自动问题识别
      - 生成改进建议

    notes: |
      参考 github_mining/verification/ 的报告格式

  - id: "P4-001"
    title: "批量处理和数据库生成"
    priority: "P1"
    status: "pending"
    estimate: "2-3天"
    dependencies: ["P1-001", "P1-002", "P1-003", "P2-001"]

    description: |
      批量处理所有 462 个学生：
      1. 深度信息提取
      2. 综合评分
      3. 分层分类
      4. 生成最终数据库

    output:
      - "lamda_students_complete.json"
      - "lamda_students_tier_a.json"  # Top 10%
      - "lamda_students_tier_b.json"  # Next 30%
      - "lamda_students_tier_c.json"  # Rest 60%

    acceptance_criteria:
      - 100% 处理完成
      - Tier A 候选人准确率 > 85%
      - 所有数据字段完整

    implementation_details: |
      使用 multiprocessing 加速：
      1. 并行处理多个学生
      2. 进度条和日志
      3. 错误处理和重试
      4. 中间结果保存（每50个保存一次）

    notes: |
      这是最耗时的部分
      预计处理时间：2-3天（462个学生）

  - id: "P4-002"
    title: "智能推荐和匹配系统"
    priority: "P3"
    status: "pending"
    estimate: "1-2周"
    dependencies: ["P4-001"]

    description: |
      实现职位匹配和候选人推荐：
      1. 职位描述解析器（提取技能、经验要求）
      2. 技能匹配引擎（计算匹配度）
      3. 智能排序和推荐
      4. 生成推荐报告

    output:
      - "job_matching_engine.py"
      - 推荐系统 Web UI（可选）

    acceptance_criteria:
      - 匹配度计算准确
      - 推荐 Top 10 候选人相关性强

    notes: |
      这是最终目标，可以分阶段实现
      先做命令行版本，再做 Web UI

timeline:
  week1:
    - "Day 1-2": 深度信息提取器 (P1-001)
    - "Day 3": Google Scholar 提取器 (P1-002)
    - "Day 4": GitHub 深度分析器 (P1-003)
    - "Day 5": 测试和调整"

  week2:
    - "Day 1-3": 综合评分系统 (P2-001)
    - "Day 4": 智能速率限制 (P2-003)
    - "Day 5": 测试和校准

  week3:
    - "Day 1": 分阶段流水线 (P3-001)
    - "Day 2-3": 批量处理 (P4-001)
    - "Day 4-5": 验证和报告

  week4+:
    - 持续优化
    - 推荐系统 (P4-002)
    - 反馈和迭代

risks:
  technical:
    - risk: "Google Scholar 反爬虫"
      mitigation: "使用随机延迟、限制请求频率、使用第三方 API"

    - risk: "LinkedIn 难以爬取"
      mitigation: "手动补充、降低优先级、使用其他渠道"

    - risk: "数据质量问题"
      mitigation: "多层验证、人工抽检、持续监控"

  operational:
    - risk: "处理时间过长"
      mitigation: "并行处理、分布式、增量更新"

    - risk: "评分不准确"
      mitigation: "多次校准、A/B 测试、人工反馈"

resources:
  available:
    - 已有代码: lamda_scraper (7 个核心脚本)
    - 参考项目: github_network_miner.py
    - 数据: lamda_candidates_final_enriched.csv (462 人)

  needed:
    - Python 库: beautifulsoup4, requests, scholarly, selenium
    - API: GitHub Token, LinkedIn API (可选)
    - 时间: 2-4 周全职

  learning:
    - GitHub Miner 评分系统
    - Google Scholar 爬虫
    - LinkedIn 爬虫技术
    - 多源数据整合

success_criteria:
  primary:
    - Tier A 候选人识别准确率 > 85%
    - 数据完整性 > 85%
    - 处理效率提升 3-5 倍
    - 系统可用性 > 95%

  secondary:
    - 生成完整的候选人格案数据库
    - 实现智能推荐功能
    - 建立持续优化机制

next_steps:
  immediate:
    - task: "创建深度信息提取器"
      action: "创建 deep_student_scraper.py"
      file: "lamda_scraper/deep_student_scraper.py"
      priority: "P0"
      estimate: "4-6小时"

    - task: "测试深度提取"
      action: "用 10 个学生测试深度提取功能"
      samples: ["周志华团队的3个学生", "其他院系的7个学生"]
      priority: "P0"
      estimate: "2小时"

  this_week:
    - 完成 P1-001, P1-002, P1-003
    - 开始 P2-001（评分系统）
    - 测试和校准评分系统

  this_month:
    - 完成 Phase 1-3
    - 批量处理所有学生
    - 生成 Tier 分层结果

references:
  code:
    - "github_network_miner.py" - 评分系统参考
    - "enhanced_website_scraper.py" - 爬虫基础
    - "github_email_enricher.py" - GitHub 提取
    - "redirect_utils.py" - 重定向跟随

  docs:
    - "CLARIFIED_STRATEGY.md" - 战略分析
    - "GITHUB_MINER_COMPARISON.md" - 对比分析
    - "OPTIMIZATION_RECOMMENDATIONS.md" - 优化建议
    - "QUICK_START.md" - 快速开始

notes: |
  核心洞察：两个项目目标一致（发现和评估 AI 人才），只是起点不同！
  可以大量复用 GitHub Miner 的代码和方法。

  关键成功因素：
  1. 深度信息提取（研究方向、论文是关键）
  2. 多维度综合评分（学术 > 技术 > 经验）
  3. 自动分层分类（Tier A/B/C）
  4. 联系方式完整性（邮箱 > LinkedIn > 其他）

  立即开始：从深度信息提取器开始，这是整个系统的基础！
---
