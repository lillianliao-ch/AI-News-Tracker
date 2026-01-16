# LAMDA Lab 人才数据采集工具

采集南京大学LAMDA实验室（周志华院士团队）的校友和学生数据。

## 安装依赖

```bash
pip install requests beautifulsoup4
```

## 快速开始

### 测试运行（采集5人）
```bash
python lamda_scraper.py --limit 5
```

### 完整采集（校友 + 博士生）
```bash
python lamda_scraper.py --output lamda_candidates
```

### 包含硕士生
```bash
python lamda_scraper.py --include-msc --output lamda_full
```

## 输出文件

- `lamda_candidates.csv` - Excel可直接打开
- `lamda_candidates.json` - 结构化数据，便于程序处理

## CSV字段说明

| 字段 | 说明 |
|------|------|
| 姓名 | 中文名 |
| 英文名 | 从个人主页提取 |
| 类型 | alumni/phd/msc |
| 主页 | 个人主页URL |
| 研究方向 | ML/NLP/CV等 |
| 导师 | 博士导师 |
| 博士毕业年份 | 用于判断资历 |
| 当前职位 | 职位+公司/学校 |
| 入职时间 | 用于判断跳槽窗口 |
| 顶会顶刊 | ICML×3; NeurIPS×2 格式 |
| Email | 联系邮箱 |
| LinkedIn/GitHub/Scholar | 社交链接 |
| 数据质量 | full/partial/minimal |
