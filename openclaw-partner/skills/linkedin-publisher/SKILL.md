---
name: linkedin-publisher
description: LinkedIn 内容发布。支持官方 API（合规）和浏览器方式（browser-agent）。生成文案 + 定时发布。
---

# LinkedIn Publisher Skill

## 方式 A：官方 API（推荐，合规）

### 前置条件
- LinkedIn OAuth 2.0 授权（一次性配置）
- 获取 Access Token，存入环境变量 `LINKEDIN_ACCESS_TOKEN`

### 发帖

```python
import requests

def post_to_linkedin(text: str, access_token: str, author_urn: str):
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "author": author_urn,  # "urn:li:person:YOUR_ID"
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    return requests.post(url, json=payload, headers=headers)
```

### 完整发布流程

1. Lumi 生成文案（调用 content-creator skill）
2. Telegram 推送预览 + "确认发布？"
3. 确认后调用 API 发布
4. 通知发布结果 + 帖子链接

---

## 方式 B：浏览器（browser-agent）

适用于 API 权限未配置时，或需要带图片/视频的帖子。

```python
# 调用 browser-agent 打开 LinkedIn
page.goto("https://www.linkedin.com/feed/")
# 点击"创建帖子" → 填写内容 → 发布
```

---

## 内容策略

**发帖频率**：2-3 次/周（质量优于数量）

**内容类型**：
- 行业洞察 + 招聘动态（主）
- AI 人才市场趋势（吸引候选人）
- 全球 AI 机会介绍（差异化定位）

**适合抓取的素材来源**：
- 今日紧急 JD（`SELECT * FROM jobs WHERE urgency >= 2 AND is_active = 1`）
- AI News Tracker 的日报
- GitHub Mining 发现的有趣人才信号

---

## 联系方式（文末附）

微信/电话：13585841775 | Email: lillianliao123@gmail.com
