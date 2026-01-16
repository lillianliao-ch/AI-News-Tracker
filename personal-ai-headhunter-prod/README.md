# Personal AI Headhunter

个人版 AI 猎头助手，旨在通过 AI 提升个人猎头的效率。

## 核心功能
1. **人才录入**: 支持 Excel 批量导入，自动生成 AI 画像。
2. **职位管理**: 支持 Excel 导入，自动生成 Job 画像。
3. **智能匹配**: 基于向量语义搜索和结构化标签的人岗匹配。
4. **人机协同**: 允许人工修正 AI 标签，持续优化匹配精准度。

## 技术栈
- **Frontend**: Streamlit
- **Database**: SQLite
- **Vector DB**: ChromaDB
- **AI**: OpenAI / DeepSeek API

## 快速开始

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量:
   复制 `.env.example` 为 `.env` 并填入 API Key。

3. 运行应用:
   ```bash
   streamlit run app.py
   ```


