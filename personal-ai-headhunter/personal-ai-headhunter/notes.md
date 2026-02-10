# Notes: 紧急职位批量匹配功能研究

## Sources

### Source 1: 用户需求分析
- URL: 用户对话
- Key points:
  - 用户想要查找紧急程度高的 job
  - 对这些 job 进行批量人才匹配
  - 需要生成可执行的匹配清单

### Source 2: job_search.py 代码分析
- URL: personal-ai-headhunter/job_search.py
- Key points:
  - 已有 match_job_to_candidates() 函数
  - 使用向量语义搜索
  - 结合结构化标签匹配（tech_domain, core_specialty, tech_skills）
  - 支持同义词映射（synonyms.yaml）

### Source 3: database.py 代码分析
- URL: personal-ai-headhunter/database.py
- Key points:
  - Job 表有 urgency 字段（0-3级）
  - Candidate 表有 talent_tier 字段（S/A/B/C）
  - 支持联系方式：phone, wechat_id, linkedin_url
  - pipeline_stage, follow_up_date 等运营字段

## Synthesized Findings

### 匹配算法
1. **向量语义匹配**：
   - 使用 OpenAI/DashScope embedding
   - 余弦相似度计算
   - 权重：向量搜索 + 标签匹配

2. **结构化标签**：
   - core_specialty: 核心专长
   - tech_skills: 技术栈
   - tech_domain: 技术领域
   - role_type: 角色类型
   - seniority: 资深程度

3. **同义词映射**：
   - 配置文件：config/synonyms.yaml
   - 标准化标签映射
   - 提高匹配召回率

### 验证策略
1. **逐步验证模式**：
   - 每个步骤都有验证点
   - 用户可以随时调整
   - 出问题立即停止修复

2. **质量评分系统**：
   - 高质量匹配(>0.7): 40分
   - 中等匹配(0.5-0.7): 30分
   - 联系方式完整: 30分
   - 门槛：50分良好，70分优秀

3. **数据完整性检查**：
   - 职位数量、紧急程度
   - 候选人向量覆盖
   - 联系方式完整度
   - 人才等级分布

### 输出格式设计
1. **Markdown 行动清单**：
   - 按紧急程度分组
   - 每个职位 Top 5（立即联系）
   - 候选池 Top 6-10
   - 包含联系方式、推荐理由
   - 跟进记录表格模板

2. **Excel 跟踪表**（可选）：
   - 便于团队协作
   - 状态跟踪列
   - 批量导入/导出

### 关键参数
- MIN_URGENCY: 1 (默认，只匹配紧急职位)
- TOP_K: 10 (每个职位返回10个候选人)
- MIN_SCORE: 0.3 (最低匹配分数)

## Implementation Notes

### 文件命名
- 主脚本：batch_match_urgent_jobs.py
- 查询脚本：query_urgent_jobs.py
- 报告文件：reports/urgent_jobs_matching_YYYYMMDD_HHMMSS.md

### 代码重用
- 使用现有 match_job_to_candidates() 函数
- 使用现有的向量索引机制
- 复用数据库连接逻辑

### 性能优化
- 向量缓存避免重复计算
- 同义词缓存减少加载开销
- 批量处理减少 API 调用

## Open Questions
1. 是否需要支持增量匹配（只匹配新增/更新的）？
2. 是否需要保存匹配历史记录？
3. 是否需要自动发送匹配报告给HR？
4. 是否需要支持多种导出格式（PDF、Word）？
