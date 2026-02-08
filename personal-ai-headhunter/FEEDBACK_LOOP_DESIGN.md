# 候选人反馈闭环 v2 — 全流程设计

> 最后更新: 2026-02-07
> 核心理念：给每个候选人一个**专属门户**，全旅程可见，体验极致便捷

---

## 一、核心洞察

**v1 的问题**：每个 JD 一个独立链接 → 候选人收到多个链接 → 体验碎片化
**v2 的解法**：每个候选人一个**专属页面** → 所有推荐的 JD、进度、消息都在一个地方

---

## 二、候选人视角体验（最重要）

### 候选人打开专属链接看到的：

```
┌─────────────────────────────────────────────────┐
│                                                  │
│  🎯 Hi 王先生，Lilian 为您精选了以下机会           │
│                                                  │
│  ┌─────────────────────────────────────────┐     │
│  │ 🔥 MiniMax · 多模态算法专家              │     │
│  │ 📍上海 · 💰 80-120W · 👥 HC:3           │     │
│  │                                          │     │
│  │ [查看详情]  [👍 感兴趣]  [👎 暂不考虑]    │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  ┌─────────────────────────────────────────┐     │
│  │ 字节跳动 · 搜索算法负责人                 │     │
│  │ 📍北京 · 💰 100-150W                     │     │
│  │                                          │     │
│  │ [查看详情]  [👍 感兴趣]  [👎 暂不考虑]    │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  ┌─────────────────────────────────────────┐     │
│  │ ✅ 蚂蚁集团 · 多模态研究员     进度跟踪    │     │
│  │ 📍杭州 · 💰 90-130W                      │     │
│  │                                          │     │
│  │  ✅ 已推荐给客户 (2/5)                    │     │
│  │  ⏳ 客户审简历中...                       │     │
│  │      ↓                                    │     │
│  │  ○ 安排面试                               │     │
│  │  ○ 终面                                   │     │
│  │  ○ Offer                                  │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  ─────────────────────────────────────────       │
│  💬 给 Lilian 留言                               │
│  ┌─────────────────────────────────────┐         │
│  │ 输入消息...                          │         │
│  └─────────────────────────────────────┘         │
│  [发送]                                          │
│                                                  │
│  📞 Lilian · 13585841775 · 微信同号              │
└─────────────────────────────────────────────────┘
```

### 候选人体验亮点
1. **一个链接看所有** — 不用翻聊天记录找N个链接
2. **一键反馈** — 👍/👎 按钮，无需填表（除非感兴趣才收集微信）
3. **进度可见** — 提交简历后看到实时进度（已推荐→面试→offer）
4. **异步沟通** — 随时留言，不用加微信也能沟通
5. **无需注册** — 链接即身份，不需要登录

---

## 三、全流程阶段

```
候选人视角                    你的视角                      系统动作
─────────                   ──────                       ──────
收到链接                     发出链接                      生成专属门户
  ↓                           ↓
浏览JD列表                   →看到"已浏览"                 记录浏览事件
  ↓                           ↓
点击"感兴趣"                 →看到"候选人感兴趣"            管道→replied
  ↓                           ↓
(可选)留下微信/电话           →收到联系方式                  记录到候选人DB
  ↓                           ↓
你推给客户                    标记"已推荐"                  管道→in_pipeline
  ↓                           ↓
候选人看到"已推荐给客户"      等待客户反馈                   --
  ↓                           ↓
客户安排面试                  标记"面试中"                  候选人看到进度
  ↓                           ↓
终面/Offer                   标记"offer"                   候选人看到🎉
  ↓                           ↓
（如客户拒绝）               标记"客户拒绝"                候选人看到"遗憾未通过"
                             可以推其他JD                   推新JD到门户
```

---

## 四、数据模型

### 4.1 候选人门户（CandidatePortal）

```python
class CandidatePortal(Base):
    """候选人专属门户"""
    __tablename__ = "candidate_portals"
    id = Column(Integer, primary_key=True)
    portal_code = Column(String(20), unique=True, index=True)  # 短码，如 "wangwx-a3f2"
    candidate_id = Column(Integer, index=True)       # 本地候选人ID
    candidate_name = Column(String(200))
    greeting = Column(String(500))                    # 个性化问候语
    created_at = Column(DateTime)
    last_visited_at = Column(DateTime)
    visit_count = Column(Integer, default=0)
```

### 4.2 JD推荐记录（Recommendation）

```python
class Recommendation(Base):
    """推荐给候选人的JD"""
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    portal_code = Column(String(20), index=True)
    job_id = Column(Integer)                          # 本地JD ID
    job_code = Column(String(50))
    job_title = Column(String(200))
    job_company = Column(String(200))
    job_location = Column(String(100))
    job_salary = Column(String(100))
    job_headcount = Column(Integer)
    job_description = Column(Text)
    
    # 候选人反馈
    candidate_feedback = Column(String(20))           # interested | not_interested | null
    feedback_reason = Column(String(200))             # 不感兴趣原因
    feedback_at = Column(DateTime)
    
    # 流程进度（你维护）
    pipeline_status = Column(String(20), default='recommended')
    # recommended → submitted_to_client → client_reviewing → interview_scheduled
    # → final_interview → offer → onboarded
    # → client_rejected → candidate_declined
    status_updated_at = Column(DateTime)
    status_note = Column(String(500))
    
    created_at = Column(DateTime)
    is_active = Column(Boolean, default=True)         # 可以撤回推荐
```

### 4.3 消息（PortalMessage）

```python
class PortalMessage(Base):
    """门户内的消息"""
    __tablename__ = "portal_messages"
    id = Column(Integer, primary_key=True)
    portal_code = Column(String(20), index=True)
    sender = Column(String(20))                       # candidate | recruiter
    content = Column(Text)
    created_at = Column(DateTime)
    is_read = Column(Boolean, default=False)
```

---

## 五、候选人专属页面（H5）

### URL 格式
```
jobs.rupro-consulting.com/p/{portal_code}
```
短码示例：`wangwx-a3f2`（姓名拼音缩写 + 4位随机码）

### 页面结构

```html
<!-- 问候区 -->
<header>
  Hi 王先生，以下是为您精选的机会
</header>

<!-- JD 卡片列表 -->
<section id="recommendations">
  <!-- 每个JD一张卡片，按状态分组 -->
  <!-- 如果有进度，显示进度条 -->
</section>

<!-- 留言区 -->
<section id="messages">
  <div class="chat-area">...</div>
  <input placeholder="给 Lilian 留言..." />
</section>

<!-- 底部联系方式 -->
<footer>
  Lilian · 13585841775 · 微信同号
</footer>
```

### 交互设计
- **感兴趣** → 弹出迷你表单（微信/手机，30秒完成）
- **暂不考虑** → 弹出原因选择（单选，3秒完成）
- **查看详情** → 展开JD描述（不跳转新页面）
- **留言** → 类聊天界面，即时显示

---

## 六、你的操作台（Streamlit 端）

### 6.1 候选人详情页新增

```
[候选人详情页]
├── 📋 推荐给TA的职位
│   ├── MiniMax · 多模态算法 → 👍 感兴趣 (2/5)
│   ├── 字节 · 搜索算法 → 👎 不合适(方向不匹配)
│   └── [+ 推荐新JD]  ← 选JD → 自动加到候选人门户
│
├── 📩 候选人消息 (2条新消息)
│   └── "Lilian好，MiniMax那个我很感兴趣，方便加微信聊吗？"
│
└── 🔗 专属链接: jobs.rupro-consulting.com/p/wangwx-a3f2
    [复制链接]
```

### 6.2 沟通跟进页新增

```
📩 最新反馈 (今天)
├── 🟢 王文轩 对 MiniMax·多模态 👍感兴趣 · 留微信: wxid_xxx
├── 🔴 李磊 对 字节·搜索算法 👎暂不考虑 · 方向不匹配
├── 👀 张三 浏览了门户但未操作 · 3小时前
└── 💬 赵六 留言: "想了解更多关于..."
```

### 6.3 流程管理

在候选人详情页，对每个推荐的JD可以更新进度：
```
MiniMax · 多模态算法专家
├── ✅ 候选人感兴趣 (2/5)
├── ✅ 已推荐给客户 (2/6) ← 你点击标记
├── ⏳ 客户审简历中...    ← 当前状态
│   [标记: 安排面试 / 客户拒绝]
├── ○ 面试
├── ○ 终面
└── ○ Offer
```

---

## 七、本地 ↔ 云端同步

### 推荐JD → 云端
```python
POST /api/portal/recommend
{
    "portal_code": "wangwx-a3f2",
    "job_id": 42,
    "job_title": "多模态算法专家",
    "job_company": "MiniMax",
    ...
}
```

### 更新进度 → 云端（候选人实时可见）
```python
POST /api/recommendation/{id}/status
{
    "status": "interview_scheduled",
    "note": "2月15日下午2点一面"
}
```

### 云端反馈 → 本地（Pull模式）
```python
GET /api/portal/feedbacks?since=2026-02-07T00:00:00
# 返回: 候选人反馈 + 浏览记录 + 消息
# 本地同步脚本每30分钟拉一次
```

---

## 八、开发顺序

| 阶段 | 内容 | 工作量 | 效果 |
|------|------|--------|------|
| **Step 1** | 数据模型 + 门户生成 API | 1h | 能生成专属链接 |
| **Step 2** | 候选人门户 H5 页面（JD卡片 + 反馈按钮） | 2h | 候选人能看到JD、给反馈 |
| **Step 3** | Streamlit 推荐JD + 复制链接 | 1h | 你能往门户推JD |
| **Step 4** | 反馈回传 + 管道联动 | 1h | 闭环！ |
| **Step 5** | 进度追踪（推荐→面试→offer） | 1h | 全流程可视 |
| **Step 6** | 留言功能 | 1h | 异步沟通 |

### 优先级
- **Step 1-4 是 MVP**：生成链接 → 候选人反馈 → 回传数据库
- **Step 5-6 是增强**：进度追踪和消息可以后面加

---

## 九、不感兴趣原因选项

```
○ 薪资不符合预期
○ 工作方向/技术栈不匹配
○ 目前不考虑换工作
○ 地点不合适
○ 已有更好的机会
○ 对这家公司不感兴趣
○ 其他：[自由输入]
```

这些原因会汇总到你的数据库，帮你优化匹配策略。

---

## 十、与现有 job-share-service 的关系

```
job-share-service (现有)
├── /j/{share_code}     → 单JD分享页（保留，向同行/HR分享用）
├── /admin              → 管理后台（保留）
│
├── /p/{portal_code}    → 【新增】候选人专属门户
├── /api/portal/*       → 【新增】门户相关 API
└── /api/feedbacks/*    → 【新增】反馈同步 API
```

完全兼容现有功能，新增门户是独立模块。
