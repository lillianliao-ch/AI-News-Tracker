---
name: Job Bulk Update
description: 从客户或内部文档批量更新职位信息（团队归属、HR联系人、候选人画像），支持预览模式和智能匹配
---

# 批量更新职位信息

本技能用于从客户或内部文档批量更新职位数据库，包括：
- **团队归属** (`team_name`)：职位所属的具体团队
- **HR 联系人** (`hr_contact`)：负责该职位的 HR
- **候选人画像** (`candidate_profile`)：对候选人的要求描述
- **部门关联** (`department_id`)：关联到知识库中的部门

## 场景

客户提供职位清单，需要批量更新到数据库。如果手动逐个 SQL UPDATE 容易出错且效率低。

## 工具

**脚本**: `personal-ai-headhunter/scripts/bulk_update_jobs.py`

**核心功能**:
- 通过 `job_code`（优先）或 `title`（模糊匹配）查找职位
- 批量更新多个字段
- 自动关联部门和公司 ID
- `--dry-run` 预览模式
- 错误处理：未找到的职位跳过，不中断流程

## 使用流程

### 1. 准备数据文件（JSON 格式）

```json
{
  "department": "AI Coding（代码智能）",
  "updates": [
    {
      "job_code": "BT003",
      "title": "AI Coding产品经理-Trae",
      "team_name": "AI 编程助手",
      "hr_contact": "夏丹伦 (xiadanlun@bytedance.com)",
      "candidate_profile": "IC，学历优秀，大厂/创业公司产品经验(AI产品/大体量产品经验优先)"
    },
    {
      "job_code": "BT009",
      "title": "AI编码策略产品专家",
      "team_name": "Stone-Dev Platform",
      "hr_contact": "夏丹伦 (xiadanlun@bytedance.com)",
      "candidate_profile": "策略产品，方向leader/IC，对模型/应用有强认知"
    }
  ]
}
```

**字段说明**:
- `job_code`: 职位编号（优先匹配，唯一）
- `title`: 职位名称（备选匹配，模糊查询）
- `team_name`: 团队名称
- `hr_contact`: HR 联系人
- `candidate_profile`: 候选人画像
- `department`: 部门名称（可选，脚本会自动查找 `department_id`）

### 2. 预览模式（推荐先执行）

```bash
cd personal-ai-headhunter
python3 scripts/bulk_update_jobs.py update_jobs.json --dry-run
```

**输出示例**:
```
📋 准备更新 25 个职位
🏢 部门: AI Coding（代码智能）
✅ 找到部门 ID: 10

[1/25] 处理: BT003 - AI Coding产品经理-Trae
  ✅ 找到职位: ID=420
  🔍 [DRY RUN] 将更新: {'team_name': 'AI 编程助手', 'hr_contact': '...', 'candidate_profile': '...'}
```

### 3. 执行更新

```bash
python3 scripts/bulk_update_jobs.py update_jobs.json
```

**输出示例**:
```
[1/25] 处理: BT003 - AI Coding产品经理-Trae
  ✅ 找到职位: ID=420
  ✅ 更新成功
...
==================================================
📊 更新完成
  ✅ 成功: 25
  ⏭️  跳过: 0
  ❌ 失败: 0
==================================================
```

## 更新的字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `team_name` | VARCHAR(100) | 团队名称 | "AI 编程助手"、"Stone-Dev Platform" |
| `hr_contact` | VARCHAR(200) | HR 联系人 | "夏丹伦 (xiadanlun@bytedance.com)" |
| `candidate_profile` | TEXT | 候选人画像 | "IC，学历优秀，大厂/创业公司产品经验" |
| `department_id` | INTEGER | 部门 ID（自动查找） | 10 |
| `company_id` | INTEGER | 公司 ID（自动设置） | 1 |

## 实际案例

### 修正 AI Coding 部门的 25 个职位

**修正内容**:
1. 删除了 2 个重复职位（BT001、BT002）
2. 修正了 5 个职位的团队归属（BT013-BT017 从"无归属"改为 Stone-Dev Platform）
3. 修正了 2 个职位的 HR 联系人（BT002 补充、BT025 改为张宇）
4. 补充了候选人画像信息

**最终统计**:
- AI 编程助手: 6 个职位
- Stone-Dev Platform: 9 个职位
- 开发者服务: 7 个职位
- 质量技术: 3 个职位

## 预防措施

### 1. 先预览再执行

**强制使用 `--dry-run` 预览**:
- 验证所有职位都能正确匹配
- 检查更新内容是否符合预期
- 避免批量错误

### 2. 备份数据库

在批量更新前备份数据库:
```bash
cp data/headhunter_dev.db data/headhunter_dev.db.backup_$(date +%Y%m%d)
```

### 3. 验证更新结果

更新后执行验证查询:
```sql
SELECT team_name, COUNT(*)
FROM jobs
WHERE department_id = 10
GROUP BY team_name;
```

## 常见问题

### Q: job_code 和 title 都找不到职位怎么办？
**A**: 脚本会跳过该职位，继续处理下一个，不会中断流程。最后会在总结中显示失败数量。

### Q: 如何更新多个部门的职位？
**A**: 分批处理，每个部门准备一个 JSON 文件，分别执行脚本。

### Q: 可以只更新部分字段吗？
**A**: 可以，JSON 中只需要包含需要更新的字段，未包含的字段不会修改。

### Q: 部门名称找不到怎么办？
**A**: 脚本会显示警告，但继续处理，只是不会更新 `department_id` 和 `company_id`。

## 避坑指南 (Anti-Pitfalls)

### 1. 匹配机制漏洞与精准更新
**排雷教训**：使用 `[职位名] - [公司名]` 的纯文本进行匹配时，如果系统原本标题含有不易察觉的空格或格式异构的破折号（如 `"开发 -"` vs `"开发-"`），脚本常常会因为匹配失败而跳过对应职位。
**正确规范**：在接受客户或内部团队提供需要批量修改的数据（Excel/CSV）时，**强烈要求对方直接提供系统唯一标识符 `job_code` 或内部 `id`**。脚本目前已经增强了正则剥离空格/横杠的抗干扰匹配机制，但使用 `job_code` 进行定位依然是确保 100% 精确命中和更新的最优先准则。

### 2. JSON 字段的“空字符串毒药”（前端白屏元凶）
**排雷教训**：在进行批量数据划转或重新分配部门时，如果部分职位的 `candidate_profile` 等 SQLAlchemy 底层规定为 `JSON` 的相关字段被遗留业务或爬虫非法写入了纯文本の**空字符串 `""`**，一旦这些职位从隐藏状态随新部门的选取暴露给前台时，API 在从库中转化这批数据时会直接抛出 `JSONDecodeError` 报 500 严重错误，导致前端列表瞬间发生“真空白屏挂掉”。
**正确规范**：
- 如果涉及手动后台 SQL 处理 JSON 类型的字段表，如果不需要填数据，**必须写入 SQL 安全机制的 `NULL`，绝对禁止写入 `""`**。
- 该 `bulk_update_jobs.py` 内部目前已被完全封锁保护：一切对 JSON 栏位的传输如果是空白均强制置为 NULL；如果是有效汉字内容将严格调用 `json.dumps()` 结构化保护入库，彻底避免了渲染崩溃隐患。

## 相关文件

- **脚本**: `scripts/bulk_update_jobs.py`
- **数据库**: `data/headhunter_dev.db`
- **详细文档**: `docs/job_bulk_update_process.md`
- **知识库设计**: `docs/knowledge_base_design.md`

## 职位编号规范

在批量更新时，请确保遵循 [JD Job Code Naming Convention](../jd-naming-convention/) 规范：
- 格式：`{公司前缀}{4位数字}`
- 示例：`BT0001`, `MMX0022`, `ALI0222`
- 完整前缀映射表见该规范文档
