# 🔍 快速测试 - 找到紫色按钮

## ⚠️ 关键点

**按钮只会在 LinkedIn 个人资料页面显示！**

你现在在 LinkedIn 首页，所以看不到按钮。

## 📍 正确的测试步骤

### 步骤 1：访问个人资料页面

从你的截图中，我看到有几个候选人。点击任意一个人的名字或头像，进入他们的个人资料页面。

例如，点击：
- **Phil Nan** - ByteDance - Principal Product Manager
- **Cathy Lu** - Product Manager at TikTok  
- **Yuze Sun**

或者直接访问这些 URL（从截图中看到的）：
```
https://www.linkedin.com/in/yongchun-alex-wang-871716b/
https://www.linkedin.com/in/jiamin-fan-1/
https://www.linkedin.com/in/jialson-r-1/
```

### 步骤 2：确认 URL 格式

确保浏览器地址栏显示的 URL 格式是：
```
https://www.linkedin.com/in/用户名/
```

**✅ 正确的 URL**：
- `https://www.linkedin.com/in/yongchun-alex-wang-871716b/`
- `https://www.linkedin.com/in/phil-nan/`

**❌ 错误的 URL**（不会显示按钮）：
- `https://www.linkedin.com/feed/` （首页）
- `https://www.linkedin.com/mynetwork/` （人脉页面）
- `https://www.linkedin.com/jobs/` （职位页面）

### 步骤 3：查找紫色按钮

在个人资料页面，你应该在**页面顶部**看到：

```
┌─────────────────────────────────────┐
│  紫色渐变背景容器                      │
│  ┌───────────────────────────────┐  │
│  │  🔵 Analyze with AI           │  │  ← 白色按钮
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

位置大概在：
- 个人头像和姓名下方
- "关注"、"消息"等按钮附近

## 🔧 如果还是看不到

### 方法 1：检查控制台

1. 按 `F12` 打开开发者工具
2. 切换到 **Console** 标签
3. 应该看到：
   ```
   LinkedIn-Atlas Analyzer: Content script loaded
   Initializing LinkedIn analyzer
   Analyze button injected
   ```

4. 如果没有这些日志，说明扩展没有加载

### 方法 2：手动触发

在控制台运行：
```javascript
// 检查是否在个人资料页面
console.log('Current URL:', window.location.href);
console.log('Is profile page:', window.location.href.includes('/in/'));
```

### 方法 3：强制刷新

1. 在个人资料页面按 `Ctrl+Shift+R` （Mac: `Cmd+Shift+R`）
2. 等待页面完全加载
3. 再次查找按钮

## 📸 发送调试信息

如果按照上述步骤还是看不到按钮，请：

1. 访问一个个人资料页面
2. 按 F12 打开控制台
3. 截图发给我，包含：
   - 浏览器地址栏（显示 URL）
   - 页面内容
   - 控制台日志

这样我可以帮你诊断具体问题。
