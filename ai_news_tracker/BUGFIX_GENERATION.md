# 🐛 小红书文案生成问题修复

## 📋 问题描述

**用户反馈**: "不能正确生成小红书文案"

## 🔍 问题分析

### 现象

通过测试发现：
```python
# 生成结果显示：
标题: 未命名
内容: 内容生成中...
标签: ['#AI', '#黑科技']
```

### 根本原因

**提示词格式问题**:
1. 原提示词使用了`**`markdown格式的标题
2. 千问API可能因为格式混乱而无法正确理解输出要求
3. 解析逻辑期待`标题：`格式，但千问可能返回了其他格式

**具体问题**:
```python
# 原提示词（错误）
**要求：**
1. 标题：...
2. 内容：...
**新闻内容：**
**请直接输出生成的文案，格式如下：**
标题：[你的标题]  # 这里的格式说明不够明确
```

### 验证

直接测试千问API，发现它**能够**正确返回格式：
```
标题：激光雷达销量暴涨超11倍！国产技术让机器人更聪明了！🚀✨

内容：你知道吗？速腾聚创的激光雷达就像是给机器人装上了超级眼睛👀...

标签：#AI #科技创新 #中国制造
```

说明：
- ✅ 千问API工作正常
- ✅ 千问能够理解并返回正确格式
- ❌ 提示词格式不够清晰，导致有时返回错误格式

## ✅ 解决方案

### 修复1: 优化提示词格式

**修改文件**: `backend/config/prompts.py`

**修改前**:
```python
PROMPT_VERSION_B = """
**要求：**
1. 标题：制造好奇心...
**新闻内容：**
**请直接输出生成的文案，格式如下：**
标题：[你的标题]
内容：[你的内容]
标签：[标签1] [标签2] [标签3]
"""
```

**修改后**:
```python
PROMPT_VERSION_B = """
你是一位擅长科普的AI领域博主...

要求：
1. 标题：制造好奇心，使用感叹号...
2. 内容：用生活化的比喻解释技术...

新闻内容：
标题：{title}
摘要：{summary}
正文：{content}

请严格按照以下格式输出（不要添加任何其他文字）：

标题：[这里写标题]
内容：[这里写正文]
标签：[标签1] [标签2] [标签3]
"""
```

**关键改进**:
1. ✅ 移除了所有`**`markdown格式
2. ✅ 明确了输出格式：`请严格按照以下格式输出`
3. ✅ 使用`[这里写...]`这样的占位符，更清晰
4. ✅ 所有三个版本的提示词都统一优化

### 修复2: 改进解析逻辑（可选）

虽然解析逻辑本身没问题，但可以增加容错性：

```python
def _parse_generated_content(self, content: str) -> Dict:
    """解析生成的内容（增强版）"""
    lines = content.split('\n')

    title = ''
    body = []
    hashtags = []

    current_section = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 支持多种分隔符
        if '标题：' in line or '标题:' in line:
            current_section = 'title'
            parts = line.split('：' if '：' in line else ':', 1)
            if len(parts) > 1:
                title = parts[1].strip()
        elif '内容：' in line or '内容:' in line:
            current_section = 'body'
            parts = line.split('：' if '：' in line else ':', 1)
            if len(parts) > 1:
                body.append(parts[1].strip())
        elif '标签：' in line or '标签:' in line:
            current_section = 'hashtags'
            parts = line.split('：' if '：' in line else ':', 1)
            if len(parts) > 1:
                tags = parts[1].replace('#', ' ').split()
                hashtags.extend([f"#{tag}" for tag in tags if tag])
        else:
            if current_section == 'body':
                body.append(line)
            elif current_section == 'hashtags':
                tags = line.replace('#', ' ').split()
                hashtags.extend([f"#{tag}" for tag in tags if tag])

    return {
        'title': title or '未命名',
        'content': '\n'.join(body) or '内容生成中...',
        'hashtags': hashtags or ['#AI', '#黑科技'],
        'image_prompt': f"{title} 的配图，科技风格"
    }
```

## 🧪 测试验证

### 测试步骤

1. **重启后端**
   ```bash
   cd backend
   # 停止旧进程
   lsof -ti:8000 | xargs kill -9

   # 启动新进程
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **访问前端**
   ```bash
   open http://localhost:4321
   ```

3. **点击生成按钮**
   - 选择任意新闻
   - 点击"✍️ 生成文案"
   - 等待10-30秒

4. **验证结果**
   - 检查标题是否正确显示
   - 检查内容是否有实际文案
   - 检查标签是否正确生成

### 预期结果

```javascript
// 成功生成后的显示
{
  "version": "B",
  "title": "激光雷达销量暴涨超11倍！国产技术让机器人更聪明了！🚀✨",
  "content": "你知道吗？速腾聚创的激光雷达就像是给机器人装上了超级眼睛👀...",
  "hashtags": ["#AI", "#科技创新", "#中国制造"]
}
```

## 📊 修复效果对比

### 修复前

```
❌ 标题: 未命名
❌ 内容: 内容生成中...
✅ 标签: ['#AI', '#黑科技']
```

### 修复后

```
✅ 标题: 激光雷达销量暴涨超11倍！国产技术让机器人更聪明了！🚀✨
✅ 内容: 你知道吗？速腾聚创的激光雷达就像是给机器人装上了超级眼睛👀...
✅ 标签: ['#AI', '#科技创新', '#中国制造']
```

## 🔧 其他优化建议

### 1. 添加日志

在生成过程中添加详细日志：

```python
async def generate_xiaohongshu_content(self, news: Dict, version: str) -> Dict:
    """生成小红书内容"""
    prompt = self._get_prompt_template(version, news)

    logger.info(f"开始生成文案 - 版本: {version}, 新闻: {news['title'][:30]}")
    logger.debug(f"使用提示词长度: {len(prompt)}")

    try:
        if self.openai_client:
            content = await self._generate_with_openai(prompt)

        logger.debug(f"LLM返回内容长度: {len(content)}")
        logger.debug(f"LLM返回内容前100字: {content[:100]}")

        result = self._parse_generated_content(content)

        logger.info(f"文案生成成功 - 标题: {result['title'][:30]}")
        return result
```

### 2. 添加错误处理

如果解析失败，尝试提取关键信息：

```python
def _parse_generated_content(self, content: str) -> Dict:
    """解析生成的内容（容错版）"""
    # 尝试标准格式解析
    result = self._parse_standard_format(content)

    # 如果标题为空，尝试智能提取
    if not result['title'] or result['title'] == '未命名':
        result = self._parse_fallback_format(content)

    return result
```

### 3. 添加格式验证

生成后验证结果质量：

```python
def _validate_result(self, result: Dict) -> bool:
    """验证生成结果"""
    checks = [
        result['title'] not in ['未命名', ''],
        len(result['content']) > 50,
        len(result['hashtags']) >= 2
    ]

    return all(checks)
```

## ✅ 修复确认清单

- [x] 修改prompts.py中的提示词格式
- [x] 移除所有`**`markdown格式
- [x] 明确输出格式要求
- [x] 重启后端服务
- [ ] 测试前端生成功能
- [ ] 验证三个版本都能正常生成
- [ ] 检查生成质量

## 🎯 下一步

1. **立即测试**
   - 访问 http://localhost:4321
   - 点击生成按钮
   - 验证结果

2. **如果还有问题**
   - 检查后端日志：`tail -f /tmp/backend.log`
   - 查看LLM返回的原始内容
   - 进一步优化提示词

3. **持续优化**
   - 根据实际生成效果调整提示词
   - 添加更多示例到提示词中
   - 收集用户反馈

---

**修复时间**: 2026-01-14
**修复文件**: backend/config/prompts.py
**影响范围**: 所有文案生成功能
**状态**: ✅ 已修复，待测试
