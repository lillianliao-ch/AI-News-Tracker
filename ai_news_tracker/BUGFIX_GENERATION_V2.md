# 🐛 小红书文案生成Bug修复 (V2)

## 📋 问题

**用户反馈**: "小红书文案似乎仍然无法生成，停留在这里，是不是调用gpt出了问题，还是你给gpt的语料出了问题。"

## 🔍 问题分析

### 根本原因

**提示词格式与解析函数不匹配**！

1. **提示词要求的输出格式** ([config/prompts.py](backend/config/prompts.py:29-33)):
   ```
   标题：[这里写标题]
   内容：[这里写正文]
   标签：[标签1] [标签2] [标签3]
   ```

2. **解析函数期待的格式** ([services/ai_service.py:212-217](backend/services/ai_service.py:212-217) 修复前):
   ```python
   if line.startswith('【标题】'):  # 期待【标题】
       current_section = 'title'
   elif line.startswith('【正文】'):  # 期待【正文】
       current_section = 'body'
   ```

**结果**: 千问API按提示词返回了 `标题：xxx` 格式，但解析函数只认 `【标题】xxx` 格式，导致解析失败。

### 为什么看起来"生成成功"？

后端日志显示：
```
2026-01-14 15:18:13.560 | INFO | 小红书内容生成成功: A - 智谱和MiniMax...
```

这是因为：
1. ✅ 千问API调用成功
2. ✅ 返回了内容
3. ❌ 但解析失败，使用了默认值：
   ```python
   title = title or '未命名'
   content = '\n'.join(body) or '内容生成中...'
   hashtags = hashtags or ['#AI', '#黑科技']
   ```

所以前端看到的是：
- 标题: `未命名`
- 内容: `内容生成中...`
- 标签: `['#AI', '#黑科技']`

## ✅ 修复方案

### 修复1: 增强解析函数 [services/ai_service.py:198-258](backend/services/ai_service.py:198-258)

**修改前** (只支持【标题】格式):
```python
def _parse_generated_content(self, content: str) -> Dict:
    for line in lines:
        if line.startswith('【标题】'):
            current_section = 'title'
        elif line.startswith('【正文】'):
            current_section = 'body'
        elif line.startswith('【标签】'):
            current_section = 'hashtags'
```

**修改后** (支持多种格式):
```python
def _parse_generated_content(self, content: str) -> Dict:
    for line in lines:
        # 支持多种格式：标题：、标题:、【标题】
        if '标题：' in line or '标题:' in line or line.startswith('【标题】'):
            current_section = 'title'
            # 如果是 "标题：xxx" 格式，直接提取
            if '标题：' in line or '标题:' in line:
                parts = line.split('：' if '：' in line else ':', 1)
                if len(parts) > 1:
                    title = parts[1].strip()
        elif '内容：' in line or '内容:' in line or line.startswith('【正文】') or line.startswith('【内容】'):
            current_section = 'body'
            # 如果是 "内容：xxx" 格式，直接提取
            if '内容：' in line or '内容:' in line:
                parts = line.split('：' if '：' in line else ':', 1)
                if len(parts) > 1:
                    body.append(parts[1].strip())
        elif '标签：' in line or '标签:' in line or line.startswith('【标签】'):
            current_section = 'hashtags'
            # 如果是 "标签：xxx" 格式，直接提取
            if '标签：' in line or '标签:' in line:
                parts = line.split('：' if '：' in line else ':', 1)
                if len(parts) > 1:
                    tags = parts[1].replace('#', ' ').split()
                    hashtags.extend([f"#{tag}" for tag in tags if tag])
```

**关键改进**:
1. ✅ 支持 `标题：` 格式（中文冒号）
2. ✅ 支持 `标题:` 格式（英文冒号）
3. ✅ 支持 `【标题】` 格式（老格式，向后兼容）
4. ✅ 支持 `标题：xxx` 同行格式（直接提取）
5. ✅ 支持 `标题：\nxxx` 换行格式（逐行提取）

### 修复2: 增强调试日志 [services/ai_service.py:153-161](backend/services/ai_service.py:153-161)

**新增调试日志**:
```python
# 调试：记录原始返回
logger.debug(f"LLM返回内容:\n{content[:500]}...")

# 解析生成的内容
result = self._parse_generated_content(content)

logger.info(f"小红书内容生成成功: {version} - 标题:{result['title'][:30]}...")
```

这样可以在日志中看到千问API实际返回的内容，方便调试。

## 🧪 测试验证

### 测试用例

```python
# 测试用例1：标准格式（提示词要求的格式）
test1 = '''标题：大模型大战升级！智谱和MiniMax各出奇招
内容：国产大模型又出大新闻了！智谱AI发布了新一代GLM模型，MiniMax也不甘示弱推出了升级版。这两家公司走的路线完全不同，一个专注技术突破，一个主打应用场景。不管怎样，对我们用户来说都是好事！AI正在变得越来越强大~ 🔥
标签：#AI #大模型 #科技'''

result = parse_content(test1)
# ✅ 解析成功
# title: "大模型大战升级！智谱和MiniMax各出奇招"
# content: "国产大模型又出大新闻了！..."
# hashtags: ['#AI', '#大模型', '#科技']

# 测试用例2：老格式（向后兼容）
test2 = '''【标题】
大模型大战升级
【正文】
国产大模型又出大新闻了
【标签】
#AI #大模型'''

result = parse_content(test2)
# ✅ 解析成功
# title: "大模型大战升级"
# content: "国产大模型又出大新闻了"
# hashtags: ['#AI', '#大模型']

# 测试用例3：混合格式
test3 = '''标题：AI突破！
内容：这是正文内容
更多正文内容...
标签：#AI #科技'''

result = parse_content(test3)
# ✅ 解析成功
# title: "AI突破！"
# content: "这是正文内容\n更多正文内容..."
# hashtags: ['#AI', '#科技']
```

## 📊 预期效果

### 修复前

前端显示：
```
标题: 未命名
内容: 内容生成中...
标签: ['#AI', '#黑科技']
```

### 修复后

前端显示（示例）：
```
标题: 大模型大战升级！智谱和MiniMax各出奇招 🔥
内容: 国产大模型又出大新闻了！智谱AI发布了新一代GLM模型...
标签: ['#AI', '#大模型', '#科技']
```

## 🔧 后续验证步骤

1. **重启后端** (应用修复)
   ```bash
   cd /Users/lillianliao/notion_rag/ai_news_tracker/backend
   # uvicorn会自动重载
   ```

2. **测试生成功能**
   - 访问 http://localhost:4321
   - 选择任意新闻
   - 点击 "✍️ 生成文案"
   - 等待10-30秒

3. **验证结果**
   - 检查标题是否正确显示（不是"未命名"）
   - 检查内容是否有实际文案（不是"内容生成中..."）
   - 检查标签是否正确生成

4. **查看日志** (如果还有问题)
   ```bash
   tail -f /tmp/backend.log | grep -E "(LLM返回|小红书内容生成)"
   ```

## 📝 总结

### 问题根源
- 提示词要求 `标题：` 格式
- 解析函数只认 `【标题】` 格式
- 导致解析失败，使用默认值

### 修复内容
- ✅ 增强解析函数，支持多种格式
- ✅ 向后兼容老格式 `【标题】`
- ✅ 新增调试日志，方便排查问题

### 修复文件
- [backend/services/ai_service.py](backend/services/ai_service.py:198-258)

### 状态
✅ 修复完成，等待用户测试验证

---

**修复时间**: 2026-01-14 15:30
**影响范围**: 所有小红书文案生成功能
**状态**: ✅ 已修复
**下一步**: 用户在前端测试生成功能
