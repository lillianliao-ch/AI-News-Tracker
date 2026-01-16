# Task Plan: LAMDA 顶级人才分析

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
