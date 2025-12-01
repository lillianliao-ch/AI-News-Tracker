## LinkedIn Profile Service (ContactOut)

一个最小可用的服务：给定 LinkedIn 个人主页链接，返回教育背景与工作经历。基于 ContactOut 的 LinkedIn Profile API。

参考文档： [ContactOut LinkedIn Profile API](https://api.contactout.com/#linkedin-profile-api)

### 功能
- 输入：`https://www.linkedin.com/in/<username>/`
- 输出：`name`、`headline`、`experiences[]`、`educations[]`

### 运行
1) 安装依赖
```bash
pip install -r requirements.txt
```

2) 配置环境变量（新建 `.env`）
```bash
cp env_example.txt .env
# 编辑 .env 填入 CONTACTOUT_API_TOKEN
```

3) 启动服务
```bash
uvicorn app:app --reload --port 8001
```

4) 调用示例
```bash
curl -X POST http://localhost:8001/parse \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.linkedin.com/in/<username>/"}'
```

### 配置
- `.env`
  - `CONTACTOUT_API_TOKEN=your_contactout_api_token_here`

### 备注
- 本服务仅抽取教育与经历，如果需要扩展（头像、技能、联系方式等），可直接映射 ContactOut API 的更多字段。

