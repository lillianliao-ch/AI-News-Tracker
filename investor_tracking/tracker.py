"""
投资人持仓监控系统 - MVP 实现
用于跟踪 ARK、巴菲特、佩洛西等知名投资人的持仓变化
"""

import os
import json
import sqlite3
import requests
import pandas as pd
from datetime import datetime, date
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from io import StringIO

# ==================== 配置 ====================

class Config:
    # Telegram 配置（可选）
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # 数据库路径
    DB_PATH = 'investor_holdings.db'
    
    # 重要投资人 CIK (SEC 13F)
    INVESTORS_13F = {
        'Berkshire Hathaway': '0001067983',
        'NVIDIA': '0001045810',
        'Bridgewater': '0001350694',
        'Soros Fund': '0001029160',
    }
    
    # ARK 基金
    ARK_FUNDS = ['ARKK', 'ARKW', 'ARKG', 'ARKF', 'ARKQ']

# ==================== 数据模型 ====================

@dataclass
class Holding:
    investor: str
    ticker: str
    company: str
    shares: int
    value: float
    weight: float
    date: str
    source: str

@dataclass
class HoldingChange:
    investor: str
    ticker: str
    company: str
    prev_shares: int
    curr_shares: int
    change_shares: int
    change_pct: float
    action: str  # NEW, ADD, REDUCE, EXIT
    date: str

# ==================== 数据库 ====================

class Database:
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investor TEXT NOT NULL,
                ticker TEXT NOT NULL,
                company TEXT,
                shares INTEGER,
                value REAL,
                weight REAL,
                date TEXT NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 变动记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investor TEXT NOT NULL,
                ticker TEXT NOT NULL,
                company TEXT,
                prev_shares INTEGER,
                curr_shares INTEGER,
                change_shares INTEGER,
                change_pct REAL,
                action TEXT,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_holdings(self, holdings: List[Holding]):
        """保存持仓数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for h in holdings:
            cursor.execute('''
                INSERT INTO holdings (investor, ticker, company, shares, value, weight, date, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (h.investor, h.ticker, h.company, h.shares, h.value, h.weight, h.date, h.source))
        
        conn.commit()
        conn.close()
    
    def get_latest_holdings(self, investor: str) -> List[Holding]:
        """获取指定投资人的最新持仓"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取最新日期
        cursor.execute('''
            SELECT MAX(date) FROM holdings WHERE investor = ?
        ''', (investor,))
        latest_date = cursor.fetchone()[0]
        
        if not latest_date:
            conn.close()
            return []
        
        # 获取该日期的持仓
        cursor.execute('''
            SELECT investor, ticker, company, shares, value, weight, date, source
            FROM holdings
            WHERE investor = ? AND date = ?
        ''', (investor, latest_date))
        
        holdings = []
        for row in cursor.fetchall():
            holdings.append(Holding(*row))
        
        conn.close()
        return holdings
    
    def save_changes(self, changes: List[HoldingChange]):
        """保存变动记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for c in changes:
            cursor.execute('''
                INSERT INTO changes (investor, ticker, company, prev_shares, curr_shares, 
                                     change_shares, change_pct, action, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (c.investor, c.ticker, c.company, c.prev_shares, c.curr_shares,
                  c.change_shares, c.change_pct, c.action, c.date))
        
        conn.commit()
        conn.close()

# ==================== ARK 采集器 ====================

class ARKCollector:
    """ARK 基金持仓采集器"""
    
    # 使用备用 API（arkfunds.io 非官方 API）
    API_URL = 'https://arkfunds.io/api/v2/etf/holdings'
    
    # 备用：官方 CSV（需要正确的 headers）
    BASE_URL = 'https://ark-funds.com/wp-content/uploads/funds-etf-csv/'
    FUND_FILES = {
        'ARKK': 'ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv',
        'ARKW': 'ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv',
        'ARKG': 'ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv',
        'ARKF': 'ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv',
        'ARKQ': 'ARK_AUTONOMOUS_TECH._&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv',
    }
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    def fetch_holdings(self, fund: str = 'ARKK') -> List[Holding]:
        """获取 ARK 基金持仓 - 优先使用 API，备用官方 CSV"""
        # 尝试使用 arkfunds.io API
        holdings = self._fetch_from_api(fund)
        if holdings:
            return holdings
        
        # 备用：尝试官方 CSV
        return self._fetch_from_csv(fund)
    
    def _fetch_from_api(self, fund: str) -> List[Holding]:
        """从 arkfunds.io API 获取"""
        try:
            response = requests.get(
                self.API_URL,
                params={'symbol': fund},
                headers=self.HEADERS,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            holdings = []
            
            for item in data.get('holdings', []):
                try:
                    holding = Holding(
                        investor=f'ARK_{fund}',
                        ticker=str(item.get('ticker', '')).strip(),
                        company=str(item.get('company', '')).strip(),
                        shares=int(item.get('shares', 0)),
                        value=float(item.get('market_value', 0)),
                        weight=float(item.get('weight', 0)),
                        date=str(date.today()),
                        source='arkfunds_api'
                    )
                    if holding.ticker:
                        holdings.append(holding)
                except (ValueError, KeyError):
                    continue
            
            return holdings
            
        except Exception as e:
            print(f"API fetch failed for {fund}: {e}")
            return []
    
    def _fetch_from_csv(self, fund: str) -> List[Holding]:
        """从官方 CSV 获取"""
        if fund not in self.FUND_FILES:
            return []
        
        url = self.BASE_URL + self.FUND_FILES[fund]
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
            
            # 解析 CSV
            df = pd.read_csv(StringIO(response.text))
            
            holdings = []
            for _, row in df.iterrows():
                try:
                    holding = Holding(
                        investor=f'ARK_{fund}',
                        ticker=str(row.get('ticker', '')).strip(),
                        company=str(row.get('company', '')).strip(),
                        shares=int(row.get('shares', 0)),
                        value=float(str(row.get('market value($)', 0)).replace(',', '')),
                        weight=float(str(row.get('weight(%)', 0)).replace('%', '')),
                        date=str(date.today()),
                        source='ark_official'
                    )
                    if holding.ticker:  # 过滤空行
                        holdings.append(holding)
                except (ValueError, KeyError) as e:
                    continue
            
            return holdings
            
        except Exception as e:
            print(f"Error fetching ARK {fund}: {e}")
            return []

# ==================== SEC 13F 采集器 ====================

class SEC13FCollector:
    """SEC 13F 持仓采集器 - 用于获取机构投资者季度持仓"""
    
    SEC_BASE = 'https://data.sec.gov'
    EDGAR_BASE = 'https://www.sec.gov/cgi-bin/browse-edgar'
    
    # 常用投资人 CIK
    INVESTORS = {
        'Berkshire Hathaway': '0001067983',
        'NVIDIA': '0001045810',
        'Bridgewater': '0001350694',
        'Soros Fund': '0001029160',
        'Renaissance': '0001037389',
        'Citadel': '0001423053',
        'BlackRock': '0001364742',
    }
    
    HEADERS = {
        'User-Agent': 'InvestorTracker contact@example.com',  # SEC 要求提供联系方式
        'Accept': 'application/json',
    }
    
    def get_latest_13f_filing(self, cik: str) -> Optional[dict]:
        """获取最新的 13F 提交"""
        # 标准化 CIK（10 位，前面补零）
        cik = cik.lstrip('0').zfill(10)
        
        try:
            # 获取公司提交历史
            url = f'{self.SEC_BASE}/submissions/CIK{cik}.json'
            response = requests.get(url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            filings = data.get('filings', {}).get('recent', {})
            
            # 找到最新的 13F-HR 提交
            forms = filings.get('form', [])
            accession_numbers = filings.get('accessionNumber', [])
            filing_dates = filings.get('filingDate', [])
            
            for i, form in enumerate(forms):
                if form == '13F-HR':
                    return {
                        'company': data.get('name', ''),
                        'cik': cik,
                        'accession_number': accession_numbers[i],
                        'filing_date': filing_dates[i],
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting 13F filing for CIK {cik}: {e}")
            return None
    
    def fetch_holdings(self, investor_name: str) -> List[Holding]:
        """获取指定投资人的 13F 持仓"""
        cik = self.INVESTORS.get(investor_name)
        if not cik:
            print(f"Unknown investor: {investor_name}")
            return []
        
        # 获取最新 13F 提交信息
        filing = self.get_latest_13f_filing(cik)
        if not filing:
            print(f"No 13F filing found for {investor_name}")
            return []
        
        print(f"  Found 13F filing: {filing['filing_date']}")
        
        # 解析持仓数据
        return self._parse_13f_holdings(filing, investor_name)
    
    def _parse_13f_holdings(self, filing: dict, investor_name: str) -> List[Holding]:
        """解析 13F 持仓数据"""
        cik = filing['cik'].lstrip('0')
        accession = filing['accession_number'].replace('-', '')
        
        # 先获取 filing 目录以找到正确的 XML 文件
        index_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/'
        
        try:
            response = requests.get(index_url, headers=self.HEADERS, timeout=30)
            if response.status_code != 200:
                print(f"  Failed to get filing index: {response.status_code}")
                return []
            
            # 从目录页面中提取 XML 文件链接
            import re
            files = re.findall(r'href="([^"]+\.xml)"', response.text, re.IGNORECASE)
            
            # 过滤掉 primary_doc.xml，优先使用数字命名的 XML 文件（包含实际持仓）
            xml_files = [f for f in files if 'primary_doc' not in f.lower()]
            
            holdings = []
            for file_path in xml_files:
                # 文件路径可能是相对或绝对路径
                if file_path.startswith('/'):
                    xml_url = f'https://www.sec.gov{file_path}'
                else:
                    xml_url = f'{index_url}{file_path}'
                
                try:
                    xml_resp = requests.get(xml_url, headers=self.HEADERS, timeout=30)
                    if xml_resp.status_code == 200 and 'infoTable' in xml_resp.text:
                        holdings = self._parse_xml_holdings(xml_resp.text, investor_name, filing['filing_date'])
                        if holdings:
                            print(f"  Parsed {len(holdings)} holdings from {file_path.split('/')[-1]}")
                            return holdings
                except Exception as e:
                    continue
            
            return holdings
            
        except Exception as e:
            print(f"Error getting filing: {e}")
            return []
    
    def _parse_xml_holdings(self, xml_content: str, investor_name: str, filing_date: str) -> List[Holding]:
        """解析 13F XML 格式的持仓数据"""
        import xml.etree.ElementTree as ET
        
        holdings = []
        
        try:
            # 移除命名空间以简化解析
            xml_content = xml_content.replace('xmlns=', 'xmlns_removed=')
            root = ET.fromstring(xml_content)
            
            # 查找所有 infoTable 条目
            for info_table in root.iter():
                if 'infotable' in info_table.tag.lower() and info_table.tag.lower().endswith('infotable'):
                    try:
                        # 提取字段
                        name_of_issuer = ''
                        cusip = ''
                        value = 0
                        shares = 0
                        
                        for child in info_table:
                            tag = child.tag.lower()
                            text = (child.text or '').strip()
                            
                            if 'nameofissuer' in tag:
                                name_of_issuer = text
                            elif 'cusip' in tag:
                                cusip = text
                            elif 'value' in tag:
                                try:
                                    # 13F value 已经是美元（不是千元）
                                    value = int(text)
                                except:
                                    pass
                            elif 'shrsOrPrnAmt' in child.tag:
                                # 嵌套结构：shrsOrPrnAmt -> sshPrnamt
                                for sub in child:
                                    if 'sshprnamt' in sub.tag.lower():
                                        try:
                                            shares = int(sub.text or 0)
                                        except:
                                            pass
                        
                        if name_of_issuer and shares > 0:
                            ticker = self._guess_ticker(name_of_issuer, cusip)
                            
                            holdings.append(Holding(
                                investor=f'13F_{investor_name.replace(" ", "_")}',
                                ticker=ticker,
                                company=name_of_issuer,
                                shares=shares,
                                value=float(value),
                                weight=0.0,
                                date=filing_date,
                                source='sec_13f'
                            ))
                    except Exception:
                        continue
            
            # 按公司聚合相同持仓（同一公司可能有多条记录）
            aggregated = {}
            for h in holdings:
                key = h.company
                if key in aggregated:
                    aggregated[key].shares += h.shares
                    aggregated[key].value += h.value
                else:
                    aggregated[key] = h
            
            holdings = list(aggregated.values())
            
            # 计算权重
            total_value = sum(h.value for h in holdings)
            if total_value > 0:
                for h in holdings:
                    h.weight = (h.value / total_value) * 100
            
            # 按市值排序
            holdings.sort(key=lambda x: x.value, reverse=True)
            
        except Exception as e:
            print(f"Error parsing 13F XML: {e}")
        
        return holdings
    
    def _guess_ticker(self, company_name: str, cusip: str) -> str:
        """根据公司名或 CUSIP 猜测 ticker"""
        # 常见公司映射
        ticker_map = {
            'APPLE': 'AAPL',
            'MICROSOFT': 'MSFT',
            'AMAZON': 'AMZN',
            'ALPHABET': 'GOOGL',
            'NVIDIA': 'NVDA',
            'META': 'META',
            'BERKSHIRE': 'BRK.B',
            'TESLA': 'TSLA',
            'VISA': 'V',
            'MASTERCARD': 'MA',
            'COCA-COLA': 'KO',
            'AMERICAN EXPRESS': 'AXP',
            'CHEVRON': 'CVX',
            'OCCIDENTAL': 'OXY',
            'BANK OF AMERICA': 'BAC',
            'WELLS FARGO': 'WFC',
            'MOODY': 'MCO',
            'KRAFT': 'KHC',
        }
        
        company_upper = company_name.upper()
        for key, ticker in ticker_map.items():
            if key in company_upper:
                return ticker
        
        # 如果没找到，返回公司名前几个字符
        return company_name[:5].upper().replace(' ', '')
    
    def get_investor_list(self) -> List[str]:
        """获取可用的投资人列表"""
        return list(self.INVESTORS.keys())

# ==================== 数据模型：国会交易 ====================

@dataclass
class CongressTrade:
    """国会议员交易记录"""
    politician: str
    party: str
    chamber: str  # House / Senate
    ticker: str
    company: str
    trade_date: str
    disclosure_date: str
    trade_type: str  # buy / sell
    amount_range: str  # e.g., "$1M–$5M"
    owner: str  # Self / Spouse / Joint
    source: str

# ==================== 国会交易采集器 ====================

class CongressCollector:
    """国会议员交易采集器 - 从 Capitol Trades 获取数据"""
    
    BASE_URL = 'https://www.capitoltrades.com'
    
    # 重要国会议员 ID
    POLITICIANS = {
        'Nancy Pelosi': 'P000197',
        'Dan Crenshaw': 'C001120',
        'Tommy Tuberville': 'T000278',
        'Josh Gottheimer': 'G000583',
        'Marjorie Taylor Greene': 'G000596',
        'Michael McCaul': 'M001157',
        'Pat Fallon': 'F000472',
        'David Rouzer': 'R000603',
    }
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    def fetch_trades(self, politician_name: str, limit: int = 50) -> List[CongressTrade]:
        """获取指定国会议员的交易记录"""
        pol_id = self.POLITICIANS.get(politician_name)
        if not pol_id:
            print(f"Unknown politician: {politician_name}")
            print(f"Available: {', '.join(self.POLITICIANS.keys())}")
            return []
        
        url = f'{self.BASE_URL}/trades?politician={pol_id}'
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=30)
            if response.status_code != 200:
                print(f"Failed to fetch trades: {response.status_code}")
                return []
            
            return self._parse_trades_html(response.text, politician_name)
            
        except Exception as e:
            print(f"Error fetching congress trades: {e}")
            return []
    
    def _parse_trades_html(self, html: str, politician_name: str) -> List[CongressTrade]:
        """解析交易页面 HTML - 提取 Nuxt.js 嵌入的 JSON 数据"""
        import re
        
        trades = []
        
        try:
            # Capitol Trades 使用 Nuxt.js，数据中的引号被转义
            # 先 unescape 再用简单正则提取
            unescaped = html.replace('\\"', '"').replace('\\\\"', '"')
            
            # 提取各字段
            ticker_pattern = r'"issuerTicker":"([A-Z]+):US"'
            company_pattern = r'"issuerName":"([^"]+)"'
            type_pattern = r'"txType":"(buy|sell)"'
            date_pattern = r'"txDate":"([^"]+)"'
            
            tickers = re.findall(ticker_pattern, unescaped)
            companies = re.findall(company_pattern, unescaped)
            types = re.findall(type_pattern, unescaped, re.IGNORECASE)
            dates = re.findall(date_pattern, unescaped)
            
            print(f"  Found: {len(tickers)} trades")
            
            # 组合结果
            for i, ticker in enumerate(tickers[:50]):
                company = companies[i] if i < len(companies) else ''
                tx_type = types[i] if i < len(types) else 'unknown'
                tx_date = dates[i] if i < len(dates) else ''
                
                trades.append(CongressTrade(
                    politician=politician_name,
                    party='Democrat' if 'Pelosi' in politician_name else 'Unknown',
                    chamber='House',
                    ticker=ticker,
                    company=company,
                    trade_date=tx_date[:10] if len(tx_date) >= 10 else tx_date,
                    disclosure_date='',
                    trade_type=tx_type.lower(),
                    amount_range='N/A',
                    owner='Spouse' if 'Pelosi' in politician_name else 'Unknown',
                    source='capitol_trades'
                ))
            
            # 去重
            seen = set()
            unique_trades = []
            for t in trades:
                key = (t.ticker, t.trade_date, t.trade_type)
                if key not in seen:
                    seen.add(key)
                    unique_trades.append(t)
            
            return unique_trades
            
        except Exception as e:
            print(f"Error parsing trades: {e}")
            return []
    
    def fetch_recent_trades(self, limit: int = 100) -> List[CongressTrade]:
        """获取最近的国会交易（所有议员）"""
        url = f'{self.BASE_URL}/trades'
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=30)
            if response.status_code != 200:
                print(f"Failed to fetch trades: {response.status_code}")
                return []
            
            return self._parse_trades_html(response.text, 'All Congress')
            
        except Exception as e:
            print(f"Error fetching congress trades: {e}")
            return []
    
    def get_politician_list(self) -> List[str]:
        """获取可用的国会议员列表"""
        return list(self.POLITICIANS.keys())

class ChangeDetector:
    """持仓变动检测器"""
    
    def detect(self, investor: str, current: List[Holding], 
               previous: List[Holding]) -> List[HoldingChange]:
        """检测持仓变动"""
        changes = []
        
        curr_map = {h.ticker: h for h in current}
        prev_map = {h.ticker: h for h in previous}
        
        today = str(date.today())
        
        # 检测新增和增持
        for ticker, curr in curr_map.items():
            if ticker not in prev_map:
                # 新建仓
                changes.append(HoldingChange(
                    investor=investor,
                    ticker=ticker,
                    company=curr.company,
                    prev_shares=0,
                    curr_shares=curr.shares,
                    change_shares=curr.shares,
                    change_pct=float('inf'),
                    action='NEW',
                    date=today
                ))
            else:
                prev = prev_map[ticker]
                if curr.shares != prev.shares:
                    change_pct = ((curr.shares - prev.shares) / prev.shares * 100) if prev.shares else 0
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
                        date=today
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
                    date=today
                ))
        
        return changes

# ==================== 共同持仓分析 ====================

class OverlapAnalyzer:
    """共同持仓分析器"""
    
    def find_common(self, holdings_by_investor: Dict[str, List[Holding]]) -> List[dict]:
        """找出多投资人共同持仓"""
        from collections import defaultdict
        ticker_investors = defaultdict(list)
        
        for investor, holdings in holdings_by_investor.items():
            for h in holdings:
                ticker_investors[h.ticker].append({
                    'investor': investor,
                    'weight': h.weight,
                    'shares': h.shares,
                    'value': h.value,
                    'company': h.company
                })
        
        # 筛选被多人持有的股票
        common = []
        for ticker, investors in ticker_investors.items():
            if len(investors) >= 2:
                common.append({
                    'ticker': ticker,
                    'company': investors[0]['company'],
                    'num_investors': len(investors),
                    'investors': [i['investor'] for i in investors],
                    'total_value': sum(i['value'] for i in investors)
                })
        
        # 按持有人数和总市值排序
        common.sort(key=lambda x: (-x['num_investors'], -x['total_value']))
        
        return common

# ==================== 通知 ====================

class TelegramNotifier:
    """Telegram 通知器"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or Config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or Config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot_token and self.chat_id)
    
    def send(self, message: str) -> bool:
        """发送消息"""
        if not self.enabled:
            print("Telegram not configured, printing to console:")
            print(message)
            return False
        
        try:
            url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
            response = requests.post(url, json={
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            })
            return response.ok
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
    
    def format_changes(self, changes: List[HoldingChange]) -> str:
        """格式化变动消息"""
        emoji_map = {
            'NEW': '🆕',
            'ADD': '📈',
            'REDUCE': '📉',
            'EXIT': '❌'
        }
        
        lines = [f'🔔 *持仓变动提醒* ({date.today()})\n']
        
        for c in changes:
            emoji = emoji_map.get(c.action, '•')
            pct_str = f'{c.change_pct:+.1f}%' if c.change_pct != float('inf') else 'NEW'
            
            lines.append(
                f"{emoji} *{c.investor}* {c.action} `{c.ticker}`\n"
                f"   {c.company}\n"
                f"   {c.prev_shares:,} → {c.curr_shares:,} ({pct_str})\n"
            )
        
        return '\n'.join(lines)

# ==================== 主程序 ====================

class InvestorTracker:
    """投资人持仓跟踪器"""
    
    def __init__(self):
        self.db = Database()
        self.ark_collector = ARKCollector()
        self.sec13f_collector = SEC13FCollector()
        self.congress_collector = CongressCollector()
        self.change_detector = ChangeDetector()
        self.overlap_analyzer = OverlapAnalyzer()
        self.notifier = TelegramNotifier()
    
    def check_ark_changes(self, fund: str = 'ARKK') -> List[HoldingChange]:
        """检查 ARK 基金持仓变动"""
        investor = f'ARK_{fund}'
        print(f"Checking {investor}...")
        
        # 获取最新持仓
        current = self.ark_collector.fetch_holdings(fund)
        if not current:
            print(f"Failed to fetch {investor} holdings")
            return []
        
        print(f"  Fetched {len(current)} holdings")
        
        # 获取之前的持仓
        previous = self.db.get_latest_holdings(investor)
        print(f"  Previous holdings: {len(previous)}")
        
        # 检测变动
        changes = []
        if previous:
            changes = self.change_detector.detect(investor, current, previous)
            print(f"  Changes detected: {len(changes)}")
        
        # 保存最新持仓
        self.db.save_holdings(current)
        
        # 保存变动记录
        if changes:
            self.db.save_changes(changes)
        
        return changes
    
    def run_daily_check(self):
        """运行每日检查"""
        print(f"\n{'='*50}")
        print(f"Daily Check - {datetime.now()}")
        print(f"{'='*50}\n")
        
        all_changes = []
        
        # 检查所有 ARK 基金
        for fund in Config.ARK_FUNDS:
            changes = self.check_ark_changes(fund)
            all_changes.extend(changes)
        
        # 发送通知
        if all_changes:
            message = self.notifier.format_changes(all_changes)
            self.notifier.send(message)
            print(f"\n{len(all_changes)} changes notified!")
        else:
            print("\nNo changes detected.")
        
        return all_changes
    
    def analyze_common_holdings(self) -> List[dict]:
        """分析共同持仓"""
        holdings_by_investor = {}
        
        for fund in Config.ARK_FUNDS:
            investor = f'ARK_{fund}'
            holdings = self.db.get_latest_holdings(investor)
            if holdings:
                holdings_by_investor[investor] = holdings
        
        common = self.overlap_analyzer.find_common(holdings_by_investor)
        return common
    
    def print_holdings_summary(self, investor: str):
        """打印持仓摘要"""
        holdings = self.db.get_latest_holdings(investor)
        
        if not holdings:
            print(f"No holdings found for {investor}")
            return
        
        print(f"\n{investor} Holdings ({holdings[0].date}):")
        print("-" * 60)
        
        # 按权重排序
        sorted_holdings = sorted(holdings, key=lambda x: x.weight, reverse=True)
        
        for i, h in enumerate(sorted_holdings[:20], 1):
            print(f"{i:2}. {h.ticker:6} {h.company[:30]:30} {h.weight:5.2f}%")

# ==================== CLI ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='投资人持仓监控系统')
    parser.add_argument('command', choices=['check', 'holdings', 'common', '13f', 'congress', 'list-investors'],
                        help='命令: check=检查变动, holdings=查看持仓, common=共同持仓, 13f=获取13F持仓, congress=国会交易, list-investors=列出可用投资人')
    parser.add_argument('--fund', default='ARKK', help='ARK 基金代码')
    parser.add_argument('--investor', default='ARK_ARKK', help='投资人名称')
    parser.add_argument('--name', default='Berkshire Hathaway', help='13F 投资人名称')
    parser.add_argument('--politician', default='Nancy Pelosi', help='国会议员名称')
    
    args = parser.parse_args()
    
    tracker = InvestorTracker()
    
    if args.command == 'check':
        tracker.run_daily_check()
    
    elif args.command == 'holdings':
        tracker.print_holdings_summary(args.investor)
    
    elif args.command == 'common':
        common = tracker.analyze_common_holdings()
        print("\n共同持仓分析:")
        print("-" * 60)
        for item in common[:20]:
            print(f"{item['ticker']:6} {item['company'][:25]:25} "
                  f"被 {item['num_investors']} 个基金持有")
    
    elif args.command == '13f':
        print(f"\n获取 {args.name} 的 13F 持仓...")
        holdings = tracker.sec13f_collector.fetch_holdings(args.name)
        if holdings:
            print(f"\n{args.name} 13F 持仓 ({holdings[0].date}):")
            print("-" * 70)
            print(f"{'#':>3} {'Ticker':6} {'Company':<35} {'Value':>12} {'Weight':>7}")
            print("-" * 70)
            for i, h in enumerate(holdings[:30], 1):
                value_str = f"${h.value/1e9:.2f}B" if h.value >= 1e9 else f"${h.value/1e6:.0f}M"
                print(f"{i:3}. {h.ticker:6} {h.company[:35]:<35} {value_str:>12} {h.weight:>6.2f}%")
            print(f"\n总持仓: {len(holdings)} 只股票")
            total_value = sum(h.value for h in holdings)
            print(f"总市值: ${total_value/1e9:.2f}B")
            
            # 保存到数据库
            tracker.db.save_holdings(holdings)
            print(f"\n✅ 已保存到数据库")
        else:
            print("未能获取持仓数据")
    
    elif args.command == 'congress':
        print(f"\n获取 {args.politician} 的交易记录...")
        trades = tracker.congress_collector.fetch_trades(args.politician)
        if trades:
            print(f"\n{args.politician} 交易记录:")
            print("-" * 80)
            print(f"{'#':>3} {'Ticker':6} {'Company':<25} {'Type':6} {'Amount':<15} {'Date'}")
            print("-" * 80)
            for i, t in enumerate(trades[:30], 1):
                print(f"{i:3}. {t.ticker:6} {t.company[:25]:<25} {t.trade_type:6} {t.amount_range:<15} {t.trade_date}")
            print(f"\n共 {len(trades)} 笔交易")
        else:
            print("未能获取交易数据")
    
    elif args.command == 'list-investors':
        print("\n可用的 13F 投资人:")
        print("-" * 40)
        for name in tracker.sec13f_collector.get_investor_list():
            print(f"  • {name}")
        print("\n可用的国会议员:")
        print("-" * 40)
        for name in tracker.congress_collector.get_politician_list():
            print(f"  • {name}")
        print("\n使用方式: python3 tracker.py 13f --name \"Berkshire Hathaway\"")
        print("         python3 tracker.py congress --politician \"Nancy Pelosi\"")

if __name__ == '__main__':
    main()
