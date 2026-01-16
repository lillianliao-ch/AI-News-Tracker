# 千问 API 配置指南

## 概述

AI News Tracker 现已支持阿里云千问API，与你的 `personal-ai-headhunter` 项目使用相同的配置方式。

## 快速开始

### 1. 配置已完成

系统已经配置为使用千问API，配置文件位于 `backend/.env`：

```env
# 千问配置（与 personal-ai-headhunter 一致）
OPENAI_API_KEY=sk-4e2bb9108e1541f9b7dd88855922c7a3
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 千问模型
CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max
```

### 2. 重启后端服务

```bash
# 停止当前后端
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill -9

# 启动后端
cd /Users/lillianliao/notion_rag/ai_news_tracker/backend
nohup /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

### 3. 测试生成

访问 http://localhost:4321，点击任意新闻的 "生成文案" 按钮，系统会使用千问API生成小红书文案。

## 千问模型说明

### qwen-max

**特点**：
- 阿里云最强的大语言模型
- 支持复杂的推理和创作任务
- 适合生成高质量的小红书文案

**使用场景**：
- 小红书文案生成（GENERATE_MODEL）
- 新闻分类（CLASSIFY_MODEL）
- 需要高质量输出的场景

### qwen-plus

**特点**：
- 性能均衡
- 速度较快
- 成本较低

**使用场景**：
- 摘要生成（SUMMARY_MODEL）
- 简单的分类任务
- 对速度要求较高的场景

### qwen-turbo

**特点**：
- 速度最快
- 成本最低
- 适合简单任务

**使用场景**：
- 简单文本处理
- 快速响应场景

## 与 personal-ai-headhunter 的对比

| 项目 | 模型 | 用途 |
|------|------|------|
| personal-ai-headhunter | qwen-max | 简历解析、JD分析、候选人匹配 |
| AI News Tracker | qwen-max | 小红书文案生成、新闻分类 |
| personal-ai-headhunter | text-embedding-v1 | 向量嵌入 |
| AI News Tracker | - （暂不需要） | - |

两者使用相同的配置方式：
- OpenAI 兼容接口
- 相同的 BASE_URL
- 相同的 API Key

## 切换模型

### 方式 1：使用千问（推荐）

```env
# backend/.env
OPENAI_API_KEY=sk-4e2bb9108e1541f9b7dd88855922c7a3
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

CLASSIFY_MODEL=qwen-max
SUMMARY_MODEL=qwen-plus
GENERATE_MODEL=qwen-max
```

### 方式 2：使用 OpenAI

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

CLASSIFY_MODEL=gpt-4o-mini
SUMMARY_MODEL=gpt-3.5-turbo
GENERATE_MODEL=gpt-4o
```

### 方式 3：使用 Claude

```env
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

CLASSIFY_MODEL=claude-3-5-sonnet-20241022
SUMMARY_MODEL=claude-3-5-haiku-20241022
GENERATE_MODEL=claude-3-5-sonnet-20241022
```

## API 成本对比

| 模型 | 输入价格 | 输出价格 | 相对成本 |
|------|---------|---------|---------|
| qwen-max | ¥0.02/1K tokens | ¥0.06/1K tokens | 低 |
| qwen-plus | ¥0.008/1K tokens | ¥0.02/1K tokens | 很低 |
| qwen-turbo | ¥0.003/1K tokens | ¥0.006/1K tokens | 极低 |
| GPT-4o | $0.005/1K tokens | $0.015/1K tokens | 中 |
| GPT-3.5-turbo | $0.001/1K tokens | $0.002/1K tokens | 低 |
| Claude 3.5 Sonnet | $0.003/1K tokens | $0.015/1K tokens | 中 |

**结论**：千问具有极高的性价比，特别适合大规模内容生成。

## 技术实现

### OpenAI 兼容接口

千问使用 OpenAI 兼容接口，这意味着：

1. **无需额外依赖**：使用标准的 `openai` Python 包
2. **代码通用**：与 OpenAI API 完全兼容
3. **易于切换**：只需修改 BASE_URL 和 API Key

### 代码示例

```python
from openai import OpenAI

# 千问配置
client = OpenAI(
    api_key="sk-your-qwen-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 调用千问模型
response = client.chat.completions.create(
    model="qwen-max",
    messages=[
        {"role": "system", "content": "你是一个专业的内容创作者"},
        {"role": "user", "content": "生成一篇小红书文案"}
    ],
    temperature=0.8
)

print(response.choices[0].message.content)
```

## 监控和日志

### 查看后端日志

```bash
tail -f /tmp/backend.log
```

### 日志示例

成功调用千问时会看到：
```
INFO - 小红书内容生成成功: A - OpenAI发布GPT-5...
INFO - 使用模型: qwen-max
INFO - 输入tokens: 150, 输出tokens: 300
```

## 常见问题

### Q1: 千问 API 有限制吗？

**A**:
- RPM（每分钟请求数）：根据你的套餐不同
- TPM（每分钟tokens数）：根据你的套餐不同
- 日限额：根据你的套餐不同

建议查看阿里云控制台的配额设置。

### Q2: 如何获取千问 API Key？

**A**:
1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 创建 API Key
3. 复制 API Key 到 `.env` 文件

### Q3: 千问和 GPT-4 哪个更好？

**A**:
- **中文任务**：千问通常表现更好，特别是小红书文案生成
- **英文任务**：GPT-4 可能略胜一筹
- **成本**：千问远低于 GPT-4
- **速度**：千问响应更快

对于 AI News Tracker 的场景（中文内容生成），推荐使用千问。

### Q4: 如何优化生成效果？

**A**:
1. **调整提示词**：修改 `config/prompts.py` 中的提示词模板
2. **调整 temperature**：
   - 0.7-0.9：更随机，更有创意
   - 0.1-0.3：更确定，更稳定
3. **调整模型**：
   - qwen-max：最高质量
   - qwen-plus：平衡质量与速度
   - qwen-turbo：最快速度

### Q5: API Key 安全吗？

**A**:
- `.env` 文件已在 `.gitignore` 中，不会被提交
- 建议定期轮换 API Key
- 可以设置 IP 白名单限制访问

## 下一步

1. **测试生成功能**
   ```bash
   # 访问前端
   open http://localhost:4321

   # 点击任意新闻的 "生成文案" 按钮
   ```

2. **优化提示词**
   - 打开 `backend/config/prompts.py`
   - 根据生成效果调整提示词
   - 参考 [PROMPT_GUIDE.md](PROMPT_GUIDE.md)

3. **监控使用情况**
   - 查看阿里云控制台的用量统计
   - 优化模型选择以平衡成本和质量

## 参考资料

- [阿里云百炼文档](https://help.aliyun.com/zh/model-studio/)
- [千问 API 文档](https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api)
- [OpenAI API 兼容性](https://help.aliyun.com/zh/model-studio/developer-reference/compatibility-of-openai-with-dashscope)

## 总结

✅ 千问 API 已完全集成
✅ 配置与 personal-ai-headhunter 一致
✅ 支持所有千问模型（qwen-max/plus/turbo）
✅ 使用 OpenAI 兼容接口，易于切换
✅ 高性价比，特别适合中文内容生成

现在你可以使用千问 API 生成高质量的小红书文案了！🎉
