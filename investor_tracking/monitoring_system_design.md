# 知名投资人持仓监控系统设计

> **设计日期**: 2026-01-14  
> **系统目标**: 自动化跟踪巴菲特、木头姐、佩洛西等投资人持仓变化  
> **用户需求**: 尽快获知持仓变动，分析共同持仓

---

## 目录

1. [系统概述](#一系统概述)
2. [数据源分析](#二数据源分析)
3. [系统架构](#三系统架构)
4. [核心功能模块](#四核心功能模块)
5. [实现方案](#五实现方案)
6. [部署与运维](#六部署与运维)
7. [快速启动方案](#七快速启动方案)

---

## 一、系统概述

### 1.1 系统目标

| 目标 | 描述 | 优先级 |
|------|------|:------:|
| **持仓获取** | 自动抓取各投资人最新持仓 | P0 |
| **变动监控** | 检测持仓变化并及时通知 | P0 |
| **共同分析** | 分析多投资人共同持仓 | P1 |
| **收益追踪** | 计算各投资人组合收益 | P2 |
| **可视化** | 仪表盘展示持仓和变动 | P2 |

### 1.2 监控目标

| 投资人 | 类型 | 数据源 | 更新频率 | 优先级 |
|--------|------|--------|:--------:|:------:|
| **ARK Invest** | ETF | 官网每日披露 | 每日 | P0 |
| **伯克希尔/巴菲特** | 13F | SEC EDGAR | 季度 | P0 |
| **佩洛西** | 国会披露 | House.gov | 交易后 | P0 |
| **NVIDIA** | 13F | SEC EDGAR | 季度 | P1 |
| **桥水/达里奥** | 13F | SEC EDGAR | 季度 | P2 |
| **索罗斯** | 13F | SEC EDGAR | 季度 | P2 |

---

## 二、数据源分析

### 2.1 ARK Invest（最透明）

| 属性 | 详情 |
|------|------|
| **数据格式** | CSV 下载 |
| **URL** | `https://ark-funds.com/trade-notifications` |
| **更新时间** | 每个交易日 T+1 |
| **包含内容** | 每日交易（买入/卖出）、完整持仓 |
| **抓取难度** | 🟢 简单（直接下载 CSV）|

**API 端点**:
```
https://arkfunds.io/api/v2/etf/holdings?symbol=ARKK
https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv
```

### 2.2 SEC 13F（机构投资者）

| 属性 | 详情 |
|------|------|
| **数据格式** | XML/HTML |
| **URL** | `https://www.sec.gov/cgi-bin/browse-edgar` |
| **更新时间** | 季度末后 45 天 |
| **包含内容** | 超过 $1 亿的股票持仓 |
| **抓取难度** | 🟡 中等（需解析 XML）|

**重要 CIK**:
```python
INVESTORS = {
    "Berkshire Hathaway": "0001067983",
    "NVIDIA": "0001045810",
    "Bridgewater": "0001350694",
    "Soros Fund": "0001029160",
    "Renaissance": "0001037389",
}
```

### 2.3 国会议员披露

| 属性 | 详情 |
|------|------|
| **数据格式** | PDF/HTML |
| **URL** | `https://disclosures-clerk.house.gov/FinancialDisclosure` |
| **更新时间** | 交易后 45 天内 |
| **抓取难度** | 🟡 中等（需解析 PDF/HTML）|

**更好的替代数据源**:
```
https://www.capitoltrades.com/  (聚合)
https://www.quiverquant.com/congresstrading/  (API)
https://senatestockwatcher.com/  (参议员)
https://housestockwatcher.com/  (众议员)
```

### 2.4 内部人交易 (Form 4)

| 属性 | 详情 |
|------|------|
| **数据格式** | XML |
| **URL** | SEC EDGAR |
| **更新时间** | 交易后 2 个工作日 |
| **用途** | 跟踪黄仁勋等高管交易 |
| **抓取难度** | 🟡 中等 |

---

## 三、系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户层 (Frontend)                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  仪表盘   │  │  提醒通知  │  │  分析报告  │  │  API接口  │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                     应用层 (Application)                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │ 变动检测  │  │ 共同分析  │  │ 收益计算  │  │ 报告生成  │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                     数据层 (Data)                               │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │   SQLite  │  │    CSV    │  │   JSON    │  │  股价API  │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                     采集层 (Collector)                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │ ARK爬虫   │  │ SEC爬虫   │  │国会爬虫    │  │ Form4爬虫 │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 技术选型

| 层级 | 技术 | 理由 |
|------|------|------|
| **采集** | Python + requests/BeautifulSoup | 简单高效 |
| **存储** | SQLite + JSON | 轻量级，易维护 |
| **调度** | cron / APScheduler | 定时任务 |
| **通知** | 微信/Telegram/Email | 多渠道 |
| **可视化** | Streamlit / Dash | 快速搭建 |

---

## 四、核心功能模块

### 4.1 模块清单

```
investor_tracker/
├── collectors/           # 数据采集
│   ├── ark_collector.py      # ARK 每日持仓
│   ├── sec_13f_collector.py  # SEC 13F 解析
│   ├── congress_collector.py # 国会交易
│   └── form4_collector.py    # 内部人交易
├── analyzers/            # 数据分析
│   ├── change_detector.py    # 变动检测
│   ├── overlap_analyzer.py   # 共同持仓分析
│   └── return_calculator.py  # 收益计算
├── notifiers/            # 通知推送
│   ├── email_notifier.py
│   ├── wechat_notifier.py
│   └── telegram_notifier.py
├── storage/              # 数据存储
│   ├── database.py           # SQLite
│   └── models.py             # 数据模型
├── dashboard/            # 可视化
│   └── app.py                # Streamlit 应用
├── config.py             # 配置
├── scheduler.py          # 定时调度
└── main.py               # 入口
```

### 4.2 数据模型

```python
# models.py

from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Holding:
    """持仓记录"""
    investor: str           # 投资人
    ticker: str             # 股票代码
    company: str            # 公司名称
    shares: int             # 持股数量
    value: float            # 市值
    weight: float           # 占比
    date: date              # 日期
    source: str             # 数据来源

@dataclass
class Trade:
    """交易记录"""
    investor: str
    ticker: str
    company: str
    action: str             # BUY / SELL
    shares: int
    price: Optional[float]
    trade_date: date
    disclosure_date: date
    source: str

@dataclass
class HoldingChange:
    """持仓变动"""
    investor: str
    ticker: str
    company: str
    prev_shares: int
    curr_shares: int
    change_shares: int
    change_pct: float
    action: str             # NEW / ADD / REDUCE / EXIT
    date: date
```

### 4.3 核心算法：变动检测

```python
# change_detector.py

def detect_changes(investor: str, current: list, previous: list) -> list:
    """
    检测持仓变动
    
    Returns:
        List[HoldingChange]: 变动列表
    """
    changes = []
    
    curr_map = {h.ticker: h for h in current}
    prev_map = {h.ticker: h for h in previous}
    
    # 检测新增和增持
    for ticker, curr in curr_map.items():
        if ticker not in prev_map:
            changes.append(HoldingChange(
                investor=investor,
                ticker=ticker,
                company=curr.company,
                prev_shares=0,
                curr_shares=curr.shares,
                change_shares=curr.shares,
                change_pct=float('inf'),
                action='NEW',
                date=curr.date
            ))
        else:
            prev = prev_map[ticker]
            if curr.shares != prev.shares:
                change_pct = (curr.shares - prev.shares) / prev.shares * 100
                action = 'ADD' if curr.shares > prev.shares else 'REDUCE'
                changes.append(HoldingChange(
                    investor=investor,
                    ticker=ticker,
                    company=curr.company,
                    prev_shares=prev.shares,
                    curr_shares=curr.shares,
                    change_shares=curr.shares - prev.shares,
                    change_pct=change_pct,
                    action=action,
                    date=curr.date
                ))
    
    # 检测清仓
    for ticker, prev in prev_map.items():
        if ticker not in curr_map:
            changes.append(HoldingChange(
                investor=investor,
                ticker=ticker,
                company=prev.company,
                prev_shares=prev.shares,
                curr_shares=0,
                change_shares=-prev.shares,
                change_pct=-100.0,
                action='EXIT',
                date=current[0].date if current else prev.date
            ))
    
    return changes
```

### 4.4 核心算法：共同持仓分析

```python
# overlap_analyzer.py

def find_common_holdings(holdings_by_investor: dict) -> list:
    """
    找出多投资人共同持仓
    
    Args:
        holdings_by_investor: {investor: [holdings]}
    
    Returns:
        List[dict]: 共同持仓列表
    """
    # 统计每只股票被多少投资人持有
    ticker_investors = defaultdict(list)
    
    for investor, holdings in holdings_by_investor.items():
        for h in holdings:
            ticker_investors[h.ticker].append({
                'investor': investor,
                'weight': h.weight,
                'shares': h.shares,
                'value': h.value
            })
    
    # 筛选被多人持有的股票
    common = []
    for ticker, investors in ticker_investors.items():
        if len(investors) >= 2:
            common.append({
                'ticker': ticker,
                'num_investors': len(investors),
                'investors': investors,
                'total_value': sum(i['value'] for i in investors)
            })
    
    # 按持有人数和总市值排序
    common.sort(key=lambda x: (-x['num_investors'], -x['total_value']))
    
    return common
```

---

## 五、实现方案

### 5.1 ARK 采集器（每日）

```python
# collectors/ark_collector.py

import requests
import pandas as pd
from datetime import date

ARK_FUNDS = {
    'ARKK': 'ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv',
    'ARKW': 'ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv',
    'ARKG': 'ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv',
}

BASE_URL = 'https://ark-funds.com/wp-content/uploads/funds-etf-csv/'

def fetch_ark_holdings(fund: str = 'ARKK') -> pd.DataFrame:
    """获取 ARK 基金持仓"""
    url = BASE_URL + ARK_FUNDS[fund]
    response = requests.get(url)
    response.raise_for_status()
    
    # 解析 CSV
    from io import StringIO
    df = pd.read_csv(StringIO(response.text))
    
    # 标准化列名
    df = df.rename(columns={
        'ticker': 'ticker',
        'company': 'company', 
        'shares': 'shares',
        'market value($)': 'value',
        'weight(%)': 'weight'
    })
    
    df['investor'] = f'ARK_{fund}'
    df['date'] = date.today()
    df['source'] = 'ark_official'
    
    return df

def fetch_ark_trades() -> pd.DataFrame:
    """获取 ARK 每日交易"""
    # 订阅邮件或访问交易通知页面
    url = 'https://ark-funds.com/trade-notifications'
    # ... 解析交易数据
    pass
```

### 5.2 SEC 13F 采集器（季度）

```python
# collectors/sec_13f_collector.py

import requests
from xml.etree import ElementTree as ET

SEC_BASE = 'https://www.sec.gov'

def fetch_13f_filings(cik: str, count: int = 5) -> list:
    """获取最新的 13F 提交"""
    url = f'{SEC_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F-HR&dateb=&owner=include&count={count}&output=atom'
    
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    root = ET.fromstring(response.content)
    
    filings = []
    for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        link = entry.find('{http://www.w3.org/2005/Atom}link').get('href')
        updated = entry.find('{http://www.w3.org/2005/Atom}updated').text
        filings.append({'title': title, 'link': link, 'date': updated})
    
    return filings

def parse_13f_holdings(filing_url: str) -> pd.DataFrame:
    """解析 13F 持仓表"""
    # 1. 获取 filing index page
    # 2. 找到 infotable.xml
    # 3. 解析持仓数据
    pass
```

### 5.3 国会交易采集器

```python
# collectors/congress_collector.py

import requests

# 使用第三方聚合 API
QUIVER_API = 'https://api.quiverquant.com/beta/live/congresstrading'
CAPITOL_TRADES = 'https://www.capitoltrades.com/api/trades'

def fetch_congress_trades(politician: str = None) -> list:
    """获取国会议员交易"""
    # 方式 1: QuiverQuant API (需要 API key)
    # 方式 2: 爬取 CapitolTrades
    # 方式 3: 爬取 House.gov 官方披露
    
    trades = []
    
    # 示例：使用 CapitolTrades
    response = requests.get(
        CAPITOL_TRADES,
        params={'politician': politician} if politician else {}
    )
    
    if response.ok:
        data = response.json()
        for trade in data['trades']:
            trades.append({
                'politician': trade['politician'],
                'ticker': trade['ticker'],
                'action': trade['type'],
                'amount': trade['amount'],
                'trade_date': trade['txDate'],
                'disclosure_date': trade['filedDate']
            })
    
    return trades
```

### 5.4 通知模块

```python
# notifiers/telegram_notifier.py

import requests

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f'https://api.telegram.org/bot{bot_token}'
    
    def send(self, message: str):
        """发送 Telegram 消息"""
        url = f'{self.base_url}/sendMessage'
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload)
        return response.ok

def format_change_alert(changes: list) -> str:
    """格式化变动提醒消息"""
    lines = ['🔔 *持仓变动提醒*\n']
    
    for c in changes:
        emoji = {
            'NEW': '🆕',
            'ADD': '📈',
            'REDUCE': '📉',
            'EXIT': '❌'
        }[c.action]
        
        lines.append(
            f"{emoji} *{c.investor}* {c.action} `{c.ticker}`\n"
            f"   {c.prev_shares:,} → {c.curr_shares:,} "
            f"({c.change_pct:+.1f}%)"
        )
    
    return '\n'.join(lines)
```

### 5.5 调度器

```python
# scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from collectors import ark_collector, sec_13f_collector, congress_collector
from analyzers import change_detector
from notifiers import telegram_notifier

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=9, minute=30, day_of_week='mon-fri')
def daily_ark_check():
    """每日检查 ARK 持仓变动"""
    print("Checking ARK holdings...")
    
    # 获取最新持仓
    current = ark_collector.fetch_ark_holdings('ARKK')
    
    # 获取昨日持仓（从数据库）
    previous = database.get_latest_holdings('ARK_ARKK')
    
    # 检测变动
    changes = change_detector.detect_changes('ARK_ARKK', current, previous)
    
    # 保存最新持仓
    database.save_holdings(current)
    
    # 发送通知
    if changes:
        message = format_change_alert(changes)
        telegram_notifier.send(message)

@scheduler.scheduled_job('cron', day=15, hour=10)
def monthly_13f_check():
    """每月 15 日检查 13F 更新"""
    print("Checking 13F filings...")
    
    for name, cik in INVESTORS.items():
        filings = sec_13f_collector.fetch_13f_filings(cik)
        # 检查是否有新的 filing
        # ...

if __name__ == '__main__':
    scheduler.start()
```

---

## 六、部署与运维

### 6.1 部署方式

| 方式 | 适用场景 | 优缺点 |
|------|---------|--------|
| **本地定时任务** | 个人使用 | 简单，但需保持开机 |
| **云函数** | 轻量级 | 按需运行，成本低 |
| **云服务器** | 持续运行 | 完整控制，成本中 |
| **Railway/Vercel** | 快速部署 | 易用，有免费额度 |

### 6.2 推荐部署：Railway

```yaml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python scheduler.py"
restartPolicyType = "ON_FAILURE"

[env]
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
```

### 6.3 监控与告警

| 监控项 | 方法 |
|--------|------|
| 任务执行状态 | 日志 + Telegram 通知 |
| 数据源可用性 | 健康检查 |
| 异常处理 | try-catch + 告警 |

---

## 七、快速启动方案

### 7.1 MVP 功能

| 功能 | 优先级 | 预计工时 |
|------|:------:|:-------:|
| ARK 每日持仓抓取 | P0 | 2h |
| 变动检测 | P0 | 2h |
| Telegram 通知 | P0 | 1h |
| 本地 SQLite 存储 | P0 | 2h |
| **MVP 总计** | — | **7h** |

### 7.2 快速启动步骤

```bash
# 1. 创建项目
mkdir investor_tracker && cd investor_tracker

# 2. 初始化环境
python -m venv venv
source venv/bin/activate
pip install requests pandas apscheduler python-telegram-bot

# 3. 创建配置
cat > config.py << EOF
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
EOF

# 4. 运行
python main.py
```

### 7.3 立即可用的替代方案

如果不想自己开发，可以使用现有服务：

| 服务 | 类型 | 特点 | 链接 |
|------|------|------|------|
| **ARK 邮件订阅** | 免费 | 每日交易邮件 | ark-funds.com |
| **WhaleWisdom** | 部分免费 | 13F 变动提醒 | whalewisdom.com |
| **CapitolTrades** | 免费 | 国会交易跟踪 | capitoltrades.com |
| **OpenInsider** | 免费 | 内部人交易 | openinsider.com |
| **Unusual Whales** | 付费 | 综合跟踪 | unusualwhales.com |
| **Quiver Quant** | 部分免费 | API 访问 | quiverquant.com |

### 7.4 推荐快速启动

> [!TIP]
> **最快方式**: 
> 1. 订阅 ARK 每日交易邮件（免费）
> 2. 设置 WhaleWisdom 13F 提醒（免费）
> 3. 关注 CapitolTrades 佩洛西页面
> 
> 这样无需开发即可获得核心功能！

---

## 八、扩展功能（后续迭代）

### Phase 2: 分析增强

- [ ] 共同持仓自动分析报告
- [ ] 收益回测与对比
- [ ] 投资风格分析

### Phase 3: 可视化

- [ ] Streamlit 仪表盘
- [ ] 持仓变化时间线
- [ ] 交互式图表

### Phase 4: 智能化

- [ ] LLM 分析持仓变动原因
- [ ] 自动生成投资建议
- [ ] 多因子选股模型

---

## 附录：API 参考

### ARK Holdings API

```python
# arkfunds.io (非官方 API)
import requests

response = requests.get('https://arkfunds.io/api/v2/etf/holdings', params={
    'symbol': 'ARKK'
})
data = response.json()
```

### SEC EDGAR API

```python
# SEC 官方
BASE = 'https://data.sec.gov'

# 获取公司 filing
response = requests.get(
    f'{BASE}/submissions/CIK{cik}.json',
    headers={'User-Agent': 'Your Name your@email.com'}
)
```

### 股价数据 API

```python
# Yahoo Finance (yfinance)
import yfinance as yf

ticker = yf.Ticker('AAPL')
price = ticker.info['currentPrice']
history = ticker.history(period='1mo')
```

---

**设计完成日期**: 2026-01-14  
**下一步**: 根据需求选择 MVP 实现或使用现有服务
