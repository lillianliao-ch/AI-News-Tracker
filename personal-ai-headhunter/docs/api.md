# AI 猎头 API 参考文档

> **Base URL**: `http://localhost:8502`  
> **框架**: FastAPI  
> **数据库**: SQLite + SQLAlchemy  
> **调用方**: 脉脉助手插件、LinkedIn 插件、Streamlit 前端（app.py）

---

## 候选人 - 导入与同步

### `POST /api/candidate/check`

检查候选人是否已存在于数据库。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 候选人姓名 |
| school | string | | 学校名（用于姓名+学校匹配） |
| companies | string[] | | 公司名列表（用于姓名+公司匹配） |
| maimaiUserId | string | | 脉脉用户ID（优先精确匹配） |

**匹配策略**（按优先级）：
1. `maimai_id` 精确匹配（notes 字段）
2. 姓名 + 学校（education_details JSON）
3. 姓名 + 任一公司（work_experiences JSON / current_company）

**返回**: `{ exists: bool, candidateId?: int, matchType?: string }`

---

### `POST /api/candidate/import`

导入新候选人（仅新建，不会更新已有记录）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 姓名 |
| currentCompany | string | | 当前公司 |
| currentPosition | string | | 当前职位 |
| location | string | | 所在城市 |
| workExperiences | WorkExperience[] | | 工作经历列表 |
| educations | Education[] | | 教育经历列表 |
| projects | Project[] | | 项目经历列表 |
| skills | string[] | | 技能标签 |
| maimaiUserId | string | | 脉脉用户ID |
| source | string | | 来源（默认 "maimai"） |
| sourceUrl | string | | 来源页面URL |
| experienceYears | int | | 工作年限 |
| education | string | | 最高学历 |
| gender | string | | 性别 |
| statusTags | string[] | | 状态标签 |

**自动推测**: 年龄（基于本科入学年份）、工作年限（基于最早工作年份）、最高学历  
**异步后处理**: 标签提取（extract_tags）+ 候选人门户创建  
**返回**: `{ success: bool, candidateId: int, message: string }`

---

### `POST /api/candidate/maimai-sync`

**脉脉 Upsert 同步**（推荐使用，替代 check + import 两步调用）。

请求参数与 `/api/candidate/import` 完全相同（复用 `CandidateImportRequest`）。

**行为**：
- **不存在** → 新建（同 import 逻辑）
- **已存在** → 合并更新：
  - 空字段补充：current_title、current_company、location、experience_years、education_level、gender
  - 工作经历：按 `company + position` 去重合并
  - 教育经历：按 `school` 去重合并
  - 项目经历：按 `name` 去重合并
  - 技能标签：合并去重
  - source：追加 "maimai" 标记
  - notes：追加 maimai_id、URL、状态标签

**匹配策略**: maimai_id → 姓名+学校 → 姓名+公司

**返回**:
```json
{
  "success": true,
  "action": "created | updated | unchanged",
  "candidateId": 123,
  "matchType": "maimaiUserId | name+school | name+company",
  "updatedFields": ["current_title", "work:字节跳动", "edu:清华大学"],
  "message": "已更新 3 个字段"
}
```

---

### `POST /api/candidate/linkedin-sync`

**LinkedIn Upsert 同步**（由 linkedin-contactout-scraper 插件调用）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 姓名 |
| linkedinUrl | string | ✅ | LinkedIn 个人页 URL（用于去重） |
| currentTitle | string | | 当前职位 |
| location | string | | 所在地 |
| workExperiences | WorkExperience[] | | 工作经历 |
| educations | Education[] | | 教育经历 |
| notes | string | | 备注 |

**匹配**: 按 `linkedin_url` 精确匹配（兼容有/无尾部斜杠）  
**合并逻辑**: 同 maimai-sync（空字段补充 + 经历去重合并 + source 追加）  
**返回**: `{ success, action, candidateId, updatedFields, message }`

---

## 候选人 - 数据增强

### `POST /api/candidate/{candidate_id}/re-tier`

重新 AI 评级。调用 LLM 根据候选人完整数据重新计算 talent_tier（S/A+/A/B+/B/C）。

### `POST /api/candidate/{candidate_id}/refresh-github`

刷新 GitHub 数据。重新抓取 GitHub 公开信息（repos、stars、contributions 等）。

### `GET /api/candidate/{candidate_id}/search-scholar`

搜索 Google Scholar 匹配。可选 `query` 参数自定义搜索词。

| 参数 | 类型 | 说明 |
|------|------|------|
| query | string | 搜索词（默认用候选人姓名） |

### `POST /api/candidate/{candidate_id}/fetch-scholar`

获取并保存指定 Scholar profile 的论文数据。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scholarId | string | ✅ | Google Scholar author ID |
| scholarName | string | | Scholar 显示名 |

### `GET /api/candidate/{candidate_id}`

获取候选人完整详情（JSON 格式）。

---

## 职位 (JD)

### `GET /api/jobs`

职位列表查询。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| company | string | | 按公司筛选 |
| active_only | bool | true | 只返回活跃职位 |
| limit | int | 200 | 返回数量上限 |
| has_description | bool | false | 只返回有详细描述的 |
| search | string | | 关键词搜索 |

### `GET /api/jobs/active`

返回活跃职位简要列表（用于下拉选择等）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 50 | 返回数量上限 |

### `GET /api/jobs/{job_id}`

获取职位详情。

### `GET /api/jobs/{job_id}/maimai-form`

获取脉脉职位发布表单数据（预填字段映射）。

| 参数 | 类型 | 说明 |
|------|------|------|
| email | string | 可选，附加邮箱字段 |

### `POST /api/jobs/{job_id}/publish`

标记职位已发布到指定渠道。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| channel | string | "MM" | 发布渠道（MM=脉脉, LI=LinkedIn 等） |

---

## 沟通 & 招聘管线

### `POST /api/generate-message`

AI 生成个性化沟通消息。根据候选人 profile 和目标职位，使用 LLM 生成招呼语。

### `POST /api/comm-log`

记录沟通日志。保存与候选人的沟通记录（渠道、内容、时间等）。

### `POST /api/pipeline/update`

更新招聘管线状态。设置候选人在特定职位的管线阶段。

### `GET /api/pipeline/follow-ups`

获取待跟进列表。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| date | string | 今天 | 跟进日期 (YYYY-MM-DD) |
| include_overdue | bool | true | 是否包含逾期项 |

### `GET /api/pipeline/stats`

管线统计数据（各阶段候选人数量等）。

---

## 数据模型

### WorkExperience

```json
{ "company": "", "position": "", "startDate": "", "endDate": "", "duration": "", "description": "" }
```

### Education

```json
{ "school": "", "degree": "", "major": "", "startYear": "", "endYear": "", "description": "", "tags": [] }
```

### Project

```json
{ "name": "", "time": "", "description": "" }
```
