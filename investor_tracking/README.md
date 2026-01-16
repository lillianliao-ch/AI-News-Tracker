# 投资人持仓监控系统

自动化跟踪巴菲特、木头姐、佩洛西等知名投资人的持仓变化。

## 功能

- 🔔 **变动提醒**: 自动检测持仓变化并通知（Telegram/控制台）
- 📊 **持仓分析**: 查看各投资人最新持仓
- 🔗 **共同持仓**: 分析多投资人的共同持仓
- 📈 **收益追踪**: 计算各投资人组合收益 (TODO)

## 快速开始

### 安装依赖

```bash
pip install requests pandas
```

### 基础使用

```bash
# 检查 ARK 基金持仓变动
python3 tracker.py check

# 查看指定投资人持仓
python3 tracker.py holdings --investor ARK_ARKK

# 分析共同持仓
python3 tracker.py common
```

## Telegram 通知配置

### 方式一：使用配置脚本

```bash
./setup_telegram.sh
```

### 方式二：手动配置

1. **创建 Telegram Bot**
   - 打开 Telegram，搜索 @BotFather
   - 发送 `/newbot`，按提示设置名称
   - 保存获得的 **Bot Token**

2. **获取 Chat ID**
   - 向你的 bot 发送任意消息
   - 访问 `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - 找到 `chat.id` 字段

3. **设置环境变量**（添加到 `~/.zshrc`）
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   ```

4. **重新加载配置**
   ```bash
   source ~/.zshrc
   ```

## 定时运行

### 自动安装 cron 任务

```bash
./install_cron.sh
```

这会设置每周一到周五早上 9:30 自动检查持仓变动。

### 手动设置

```bash
crontab -e
# 添加以下行（每个交易日早上 9:30）
30 9 * * 1-5 cd /path/to/investor_tracking && python3 tracker.py check
```

## 数据源

| 投资人 | 数据源 | 更新频率 | 状态 |
|--------|--------|:--------:|:----:|
| ARK Invest | arkfunds.io API | 每日 | ✅ |
| 巴菲特/伯克希尔 | SEC 13F | 季度 | ✅ |
| 索罗斯 | SEC 13F | 季度 | ✅ |
| NVIDIA | SEC 13F | 季度 | ✅ |
| Bridgewater | SEC 13F | 季度 | ✅ |
| Renaissance | SEC 13F | 季度 | ✅ |
| Citadel | SEC 13F | 季度 | ✅ |
| BlackRock | SEC 13F | 季度 | ✅ |
| Nancy Pelosi | Capitol Trades | 交易后45天 | ✅ |
| 其他国会议员 (7位) | Capitol Trades | 交易后45天 | ✅ |

## 使用方法

### CLI 命令

```bash
# 检查 ARK 持仓变动
python3 tracker.py check

# 查看 ARK 持仓
python3 tracker.py holdings --investor ARK_ARKK

# 获取巴菲特 13F 持仓
python3 tracker.py 13f --name "Berkshire Hathaway"

# 获取索罗斯持仓
python3 tracker.py 13f --name "Soros Fund"

# 获取佩洛西交易记录
python3 tracker.py congress --politician "Nancy Pelosi"

# 列出可用的投资人和国会议员
python3 tracker.py list-investors

# 分析共同持仓
python3 tracker.py common
```

### 📊 可视化仪表盘

```bash
# 安装依赖
pip install streamlit plotly

# 启动仪表盘
streamlit run dashboard.py
```

访问 http://localhost:8501 查看仪表盘，包含：
- **总览**: 关键指标和快速概览
- **ARK 持仓**: ARK 基金持仓分析和图表
- **13F 持仓**: 巴菲特等机构投资者季度持仓
- **国会交易**: 佩洛西等议员交易追踪
- **交叉信号**: 多源共同持仓分析

## 文件结构

```
investor_tracking/
├── tracker.py              # 主程序（CLI）
├── dashboard.py            # Streamlit 可视化仪表盘
├── investor_holdings.db    # SQLite 数据库
├── setup_telegram.sh       # Telegram 配置脚本
├── install_cron.sh         # 定时任务安装脚本
├── monitoring_system_design.md  # 系统设计文档
├── famous_investors_analysis.md # 投资人分析报告
└── tempus_ai_deep_dive.md      # Tempus AI 深度研究
```

## 完成进度

- [x] ARK 每日持仓抓取
- [x] 变动检测
- [x] Telegram 通知（已内置，需配置）
- [x] SEC 13F 自动解析 (7 位投资人)
- [x] 国会交易采集 (8 位议员)
- [x] Streamlit 可视化仪表盘
- [ ] 更多国会议员
- [ ] 自动化交叉信号提醒
