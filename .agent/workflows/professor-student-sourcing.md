---
description: 查找知名教授的学生及其当前去向和联系方式
---

# 教授学生搜源工作流 (Professor Student Sourcing Workflow)

## 输入参数
- `PROFESSOR_NAME`: 教授姓名（中英文）
- `UNIVERSITY`: 所在大学
- `LAB_NAME`: 实验室名称（如有）
- `YEARS_RANGE`: 搜索年份范围（默认：最近10年）

---

## Phase 1: 实验室/主页信息采集

### Step 1.1: 搜索实验室主页
// turbo
```
使用 search_web 搜索: "{PROFESSOR_NAME} {UNIVERSITY} lab homepage"
```

### Step 1.2: 解析实验室成员页面
1. 访问实验室主页，查找以下页面：
   - `/people`, `/team`, `/members`, `/students`, `/alumni`
2. 提取所有学生信息：
   - 姓名（中英文）
   - 入学/毕业年份
   - 研究方向
   - 个人主页链接
   - 当前去向（如有显示）

### Step 1.3: 保存基础名单
创建 CSV 文件，包含字段：
```
name_cn, name_en, student_type, enrollment_year, graduation_year, research_area, personal_homepage, current_status
```

---

## Phase 2: 论文合作者分析

### Step 2.1: 获取 Google Scholar
// turbo
```
使用 search_web 搜索: "{PROFESSOR_NAME} Google Scholar"
```

### Step 2.2: 提取论文第一作者
1. 筛选近10年论文
2. 识别第一作者（排除教授本人）
3. 识别频繁出现的合作者

### Step 2.3: 合并到名单
将新发现的合作者添加到基础名单，标记来源为 "paper_coauthor"

---

## Phase 3: 学位论文数据库

### Step 3.1: 中国知网搜索（国内教授）
// turbo
```
使用 search_web 搜索: "site:cnki.net 导师:{PROFESSOR_NAME}"
```

### Step 3.2: ProQuest 搜索（国外教授）
// turbo
```
使用 search_web 搜索: "site:proquest.com advisor:{PROFESSOR_NAME}"
```

### Step 3.3: 提取学位论文作者
1. 解析搜索结果
2. 提取论文作者、答辩时间、论文题目
3. 添加到名单，标记来源为 "thesis"

---

## Phase 4: 职业去向追踪

### Step 4.1: LinkedIn 搜索
对名单中每个学生：
// turbo
```
使用 search_web 搜索: "{STUDENT_NAME} {UNIVERSITY} LinkedIn"
```

提取：
- 当前公司
- 当前职位
- 所在城市
- LinkedIn 个人页面链接

### Step 4.2: 脉脉搜索（国内学生）
对名单中每个学生：
// turbo
```
使用 search_web 搜索: "{STUDENT_NAME} {UNIVERSITY} 脉脉"
```

提取：
- 当前公司
- 当前职位
- 脉脉主页链接

### Step 4.3: GitHub 搜索（技术向学生）
// turbo
```
使用 search_web 搜索: "{STUDENT_NAME} {LAB_NAME} site:github.com"
```

提取：
- GitHub 用户名
- bio 中的联系方式
- 公开邮箱

---

## Phase 5: 联系方式提取

### Step 5.1: 个人主页抓取
对有个人主页的学生：
1. 访问个人主页
2. 提取邮箱（正则匹配 `mailto:` 和常见邮箱格式）
3. 提取社交链接（Twitter, GitHub, LinkedIn）

### Step 5.2: 企业邮箱推断
对有当前公司的学生：
1. 获取公司邮箱格式（常见格式：firstname.lastname@company.com）
2. 使用 Hunter.io 或 Clearbit 验证

### Step 5.3: 学术邮箱提取
从以下来源提取：
- Google Scholar 主页
- ResearchGate 主页
- ORCID 主页
- 论文 PDF 中的通讯邮箱

---

## Phase 6: 数据整合与输出

### Step 6.1: 合并去重
1. 按姓名合并多来源数据
2. 处理同名情况（通过研究方向/年份区分）
3. 标记数据置信度

### Step 6.2: 生成最终报告
输出 CSV 文件，包含字段：
```csv
name_cn,name_en,student_type,enrollment_year,graduation_year,advisor,research_area,current_company,current_title,location,email_personal,email_work,linkedin_url,github_url,twitter_url,personal_homepage,data_sources,confidence_score
```

### Step 6.3: 生成统计摘要
输出统计信息：
- 总计发现学生数量
- 各年份分布
- 当前去向分布（学术界/工业界/创业）
- 联系方式覆盖率
- 地理分布

---

## 执行示例

```bash
# 执行搜源任务
/professor-student-sourcing PROFESSOR_NAME="周志华" UNIVERSITY="南京大学" LAB_NAME="LAMDA" YEARS_RANGE="2015-2025"
```

---

## 注意事项

1. **速率控制**: 搜索请求间隔 2-3 秒，避免被限流
2. **数据验证**: 交叉验证多来源信息
3. **隐私合规**: 仅收集公开信息，用于合规招聘目的
4. **增量更新**: 支持增量执行，避免重复抓取

---

## 常见问题处理

| 问题 | 解决方案 |
|------|----------|
| 实验室无公开名单 | 依赖论文合作者分析 |
| 学生同名 | 结合研究方向+年份+学校区分 |
| 联系方式缺失 | 尝试 GitHub bio / 论文 PDF |
| 去向不明 | 标记为 "unknown"，后续人工补充 |

---

## 🔗 关键技能参考

详细的问题解决方案和最佳实践请参考：
- [professor-student-sourcing-skills.md](./professor-student-sourcing-skills.md)

### 核心要点

1. **GitHub Profile 邮箱需要使用 browser_subagent**
   ```
   # 正确方式
   browser_subagent: Navigate to https://github.com/username and extract email
   
   # 不完整方式
   read_url_content: https://github.com/username  # 只能获取结构
   ```

2. **GitHub → 个人主页 → 邮箱 的路径**
   ```
   github.com/username 
     → 侧边栏 website 链接 
     → 访问个人主页 
     → 提取邮箱
   ```

3. **区分 URL 类型**
   - `github.com/*` → github 列
   - `linkedin.com/*` → linkedin 列
   - 其他 → personal_website 列

4. **学术评分维度**
   - Google Scholar 引用数
   - GitHub Stars/Contributions
   - 职位级别

