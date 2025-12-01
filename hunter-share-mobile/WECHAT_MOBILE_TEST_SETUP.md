# 手机微信测试环境搭建指南

## 🎯 问题说明

`localhost:4000` 只能在本机浏览器访问，手机微信无法访问。需要让手机能访问到你电脑上的开发服务器。

---

## 💡 解决方案（3种方法）

### 方案1: 使用局域网IP（最简单，推荐）⭐

**优点**: 
- 不需要安装额外工具
- 速度快
- 免费

**缺点**:
- 手机和电脑必须在同一WiFi网络
- 无法测试微信分享卡片预览

#### 步骤：

**1. 查找你的Mac电脑IP地址**

```bash
# 方法1: 使用ifconfig
ifconfig | grep "inet " | grep -v 127.0.0.1

# 方法2: 使用系统偏好设置
# 系统偏好设置 → 网络 → WiFi → 高级 → TCP/IP
# 查看 "IPv4地址"
```

你会看到类似这样的IP地址：`192.168.1.100`（你的会不同）

**2. 修改前端配置允许外部访问**

```bash
cd /Users/lillianliao/notion_rag/hunter-share-mobile/frontend

# 编辑 package.json 的 dev 脚本
# 将 "dev": "next dev"
# 改为 "dev": "next dev -H 0.0.0.0"
```

或者直接运行：

```bash
# 停止当前服务（Ctrl+C）
# 然后用新命令启动
PORT=4000 next dev -H 0.0.0.0
```

**3. 在手机浏览器/微信中访问**

假设你的IP是 `192.168.1.100`，则访问：
```
http://192.168.1.100:4000
```

**4. 测试步骤**

① 手机连接同一WiFi
② 手机浏览器打开 `http://192.168.1.100:4000`
③ 如果能访问，说明配置成功
④ 在微信中发送这个链接给自己
⑤ 点击链接在微信内打开

**注意事项**:
- ⚠️ 微信可能会提示"非微信官方网页"，点击继续访问即可
- ⚠️ 这种方式无法看到微信分享卡片的预览效果

---

### 方案2: 使用 ngrok（功能最全，推荐测试微信分享）⭐⭐⭐

**优点**:
- 提供HTTPS公网地址
- 可以测试微信分享卡片预览
- 稳定可靠

**缺点**:
- 需要注册账号
- 免费版有流量限制

#### 步骤：

**1. 安装 ngrok**

```bash
# 使用 Homebrew 安装
brew install ngrok

# 或者下载安装
# 访问 https://ngrok.com/download
```

**2. 注册并获取 authtoken（免费）**

访问 https://dashboard.ngrok.com/signup
注册后获取你的 authtoken

**3. 配置 authtoken**

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

**4. 启动 ngrok**

```bash
# 确保你的前端服务在运行（端口4000）
# 然后在新终端执行：
ngrok http 4000
```

**5. 你会看到输出：**

```
ngrok                                                                    
                                                                         
Session Status                online                                    
Account                       你的账号                                  
Version                       3.0.0                                     
Region                        Japan (jp)                                
Latency                       -                                         
Web Interface                 http://127.0.0.1:4040                    
Forwarding                    https://abc123xyz.ngrok-free.app -> http://localhost:4000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**6. 复制 Forwarding 的 HTTPS 地址**

例如：`https://abc123xyz.ngrok-free.app`

**7. 在手机微信中测试**

① 在任意微信聊天中发送这个 ngrok 链接
② 点击链接，微信内置浏览器会打开你的应用
③ 测试分享功能
④ 现在分享时生成的二维码和链接都是公网可访问的！

**8. 查看请求日志**

访问 http://127.0.0.1:4040 可以看到所有请求的详细信息

**注意事项**:
- ⚠️ ngrok 免费版域名是临时的，重启后会变
- ⚠️ 首次访问可能需要点击"Visit Site"确认
- ✅ 支持HTTPS，微信分享无警告
- ✅ 可以测试完整的微信分享卡片预览

---

### 方案3: 使用 localtunnel（最简单，不需要注册）

**优点**:
- 不需要注册
- 一行命令搞定

**缺点**:
- 不太稳定
- 有时连接较慢

#### 步骤：

**1. 全局安装 localtunnel**

```bash
npm install -g localtunnel
```

**2. 启动隧道**

```bash
# 确保你的前端服务在运行（端口4000）
lt --port 4000 --subdomain hunter-share
```

**3. 你会得到一个公网URL**

```
your url is: https://hunter-share.loca.lt
```

**4. 在微信中访问这个URL**

首次访问会有验证页面，点击确认即可

**注意事项**:
- ⚠️ 连接可能不稳定
- ⚠️ 首次访问需要确认
- ✅ 不需要注册账号

---

## 🚀 完整测试流程（推荐使用 ngrok）

### 准备阶段

```bash
# 终端1: 启动前端服务
cd /Users/lillianliao/notion_rag/hunter-share-mobile/frontend
PORT=4000 npm run dev

# 终端2: 启动 ngrok
ngrok http 4000
```

### 测试步骤

**1. 基础访问测试**
- 复制 ngrok 提供的 HTTPS 地址（如 `https://abc123.ngrok-free.app`）
- 在手机微信中打开这个地址
- 确认页面正常显示

**2. 分享功能测试**
- 点击页面上的"分享"按钮
- 查看弹窗中的链接是否变成了 ngrok 地址
- 点击"复制链接"
- 在微信聊天中粘贴并发送

**3. 二维码测试**
- 在分享弹窗中保存二维码
- 用另一台手机微信扫描
- 确认能够打开页面

**4. 微信分享卡片测试**
- 复制 ngrok 链接
- 在微信聊天中发送
- 查看是否显示漂亮的卡片预览（标题、描述）

**5. 微信内置浏览器测试**
- 在微信中打开链接
- 测试所有功能
- 特别注意复制链接功能在微信内是否正常

---

## 🔧 修改配置以支持动态URL

为了让分享功能自动使用正确的URL（localhost或ngrok），可以这样修改：

### 方法1: 使用环境变量

**创建 `.env.local` 文件**:

```bash
cd /Users/lillianliao/notion_rag/hunter-share-mobile/frontend

cat > .env.local << EOF
NEXT_PUBLIC_SITE_URL=http://localhost:4000
EOF
```

**修改 ShareButton 组件**:

在 `src/components/ShareButton.tsx` 中：

```typescript
// 获取当前页面URL（如果没有提供）
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || '';
const shareUrl = url || (typeof window !== 'undefined' ? window.location.href : siteUrl);
```

**使用 ngrok 时**:

```bash
# 修改 .env.local
NEXT_PUBLIC_SITE_URL=https://abc123.ngrok-free.app

# 重启服务
```

### 方法2: 自动检测（推荐）

组件已经使用 `window.location.href`，会自动适应当前访问的URL。

所以无需修改代码！🎉

---

## 📱 实际操作建议

### 快速开始（最推荐）

```bash
# 1. 安装 ngrok
brew install ngrok

# 2. 注册获取 token
open https://dashboard.ngrok.com/signup

# 3. 配置 token（只需一次）
ngrok config add-authtoken YOUR_TOKEN

# 4. 启动前端服务（如果没在运行）
cd /Users/lillianliao/notion_rag/hunter-share-mobile/frontend
PORT=4000 npm run dev &

# 5. 启动 ngrok
ngrok http 4000

# 6. 复制显示的 HTTPS 地址
# 例如: https://abc123xyz.ngrok-free.app

# 7. 在手机微信中打开这个地址测试
```

---

## 🐛 常见问题

### Q1: ngrok 提示 "Failed to authenticate"

**A**: authtoken 配置不正确

```bash
# 重新配置
ngrok config add-authtoken YOUR_CORRECT_TOKEN
```

### Q2: 微信提示"网页包含不安全内容"

**A**: 使用 ngrok 的 HTTPS 地址即可解决

### Q3: ngrok 地址每次都变化

**A**: 
- 免费版确实会变化
- 升级到付费版可以固定域名
- 或使用自定义域名

### Q4: 手机访问局域网IP很慢

**A**: 
- 检查防火墙设置
- 确保手机和电脑在同一网络
- 使用 ngrok 替代

### Q5: 微信不显示分享卡片预览

**A**:
- 必须使用公网HTTPS地址（ngrok）
- 确保 Open Graph 标签正确
- 微信缓存问题，可以换个链接测试

---

## ✅ 测试检查清单

完整测试流程：

- [ ] 安装并配置 ngrok
- [ ] 启动前端服务
- [ ] 启动 ngrok 获取公网地址
- [ ] 手机微信打开 ngrok 地址
- [ ] 页面正常显示
- [ ] 点击分享按钮
- [ ] 二维码生成正确
- [ ] 复制链接功能正常
- [ ] 在微信聊天中发送链接
- [ ] 查看分享卡片预览
- [ ] 点击链接在微信内打开
- [ ] 测试微信内所有功能

---

## 🎥 推荐的测试设置

**终端布局建议**:

```
┌─────────────────┬─────────────────┐
│   终端1          │   终端2          │
│   npm run dev   │   ngrok         │
│   (前端服务)     │   (内网穿透)     │
└─────────────────┴─────────────────┘
```

**浏览器标签页**:
1. http://localhost:4000 （开发测试）
2. https://abc123.ngrok-free.app （微信测试）
3. http://127.0.0.1:4040 （ngrok 控制台）

---

## 📞 需要帮助？

如果遇到任何问题：
1. 确认前端服务运行在 4000 端口
2. 确认 ngrok 正确启动
3. 查看 ngrok 控制台的请求日志
4. 检查手机网络连接

祝测试顺利！🎉

