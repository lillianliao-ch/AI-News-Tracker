---
name: xiaohongshu-publisher
description: 小红书内容生成 + 半自动发布。Lumi 生成图文文案，自动填入创作者后台，Lilian 一键确认发布。
---

# Xiaohongshu Publisher Skill

## 当前策略：半自动（内容全自动 + 发布人工确认）

小红书无官方发布 API，完全自动化有封号风险。当前最佳路径：
- **Lumi 全自动**：题目 + 正文 + 标签生成，图片 prompt 生成
- **Lilian 半分钟操作**：在 App 上点发布（或 Lumi 填好后截图确认）

---

## 内容生成流程

### 1. 确定选题

来源优先级：
- Lilian 当天提到的话题
- AI News Tracker 有价值的行业动态
- 猎头实操经验（今日简报里的有趣数据）
- `sourcing-intel` skill 发现的新面孔/趋势

### 2. 生成文案

调用 content-creator skill，参数：
- 平台：小红书
- 风格：科普干货 or 行业洞察 or 踩坑记录（根据选题）
- 字数：400-600 字
- Hashtag：6-8 个

### 3. 生成图片 Prompt

```
图片风格：clean, minimalist, Chinese social media style
内容：{主题关键词}
文字叠加：{帖子标题}
配色：暖白/米白背景，深色字体
```

---

## 浏览器填写流程（browser-agent）

```python
# 打开小红书创作者中心
page.goto("https://creator.xiaohongshu.com/publish/publish")

# 上传图片（如有）
page.set_input_files('input[type="file"]', image_path)

# 填写标题和正文
page.fill("#title-input", title)
page.fill("#content-area", body_text)

# 截图预览
page.screenshot(path="/tmp/xhs_preview.png")

# Telegram 推送预览 + "确认发布？"
notify_with_image("/tmp/xhs_preview.png", "小红书草稿预览，确认发布？")
# 等待确认 → 点击发布
```

---

## 发布频率建议

- 目标：每日 1 篇（工作日）
- 最佳发布时间：12:00-13:00 或 20:00-22:00
- 内容节奏：2 篇干货 + 1 篇互动 / 每周

---

## 数据追踪

每周看一次：
- 哪篇帖子阅读量最高？
- 哪类内容被收藏最多？
- 有没有新的粉丝 DM 求职机会？

这些数据反哺下周选题。

---

## 现阶段限制

- 个人账号无官方发布 API，完全零人工暂不可行
- 带视频的帖子自动化更复杂（待探索）
- 图片生成需要接外部图像 API（Midjourney / DALL-E / 即梦）

> 💡 **Lumi 的主动建议**：如果账号粉丝增长到一定规模（>5000），评估申请蒲公英平台，有官方调度工具可用。
