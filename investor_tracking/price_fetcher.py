"""
股价获取模块 - 使用 Yahoo Finance 获取历史和当前股价
"""

import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from tracker import Database

@dataclass
class PriceData:
    """股价数据"""
    ticker: str
    price: float
    date: str
    source: str = 'yahoo'


class PriceFetcher:
    """股价获取器 - 使用 Yahoo Finance + 本地数据库"""
    
    def __init__(self, db: Optional[Database] = None):
        self.db = db if db else Database()
        self.yf = None
        self._init_yfinance()
    
    def _init_yfinance(self):
        """初始化 yfinance"""
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            print("Warning: yfinance not installed. Run: pip install yfinance")
    
    # _init_cache_db not needed anymore
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """获取当前价格"""
        if not self.yf:
            return None
        
        try:
            stock = self.yf.Ticker(ticker)
            info = stock.info
            
            # 尝试多个字段获取价格
            price = info.get('regularMarketPrice') or \
                    info.get('currentPrice') or \
                    info.get('previousClose')
            
            # 当前价格通常不存历史表(除非是收盘)，暂不缓存或存入单独表? 
            # 用户主要关注历史回测。这里保持原样或暂不缓存。
            return price
            
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None

    def get_quote(self, ticker: str) -> Dict[str, float]:
        """获取报价信息 (价格, 涨跌幅)"""
        # ... (keep as is or optimize)
        if not self.yf:
            return {}
        
        try:
            stock = self.yf.Ticker(ticker)
            info = stock.info
            
            price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
            prev_close = info.get('previousClose')
            
            change_pct = 0.0
            if price and prev_close:
                change_pct = (price - prev_close) / prev_close * 100
            
            return {
                'price': price,
                'change_percent': change_pct
            }
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            return {}
    
    def get_historical_price(self, ticker: str, target_date: str) -> Optional[float]:
        """获取历史价格（指定日期的收盘价）"""
        pass # Not heavily used in dashboard actually, only by tracker's weight calc?
        # Let's focus on get_price_range which feeds the chart
        
    def get_price_range(self, ticker: str, start: str, end: str) -> Dict[str, float]:
        """获取日期范围内的价格"""
        # 1. 尝试从本地数据库获取
        local_data = self.db.get_price_history(ticker, start, end)
        if local_data:
            # 简单判断：如果有数据，就认为“足够”？
            # 或者判断是否覆盖了 start/end? (Weekends exist, so strict check is hard)
            # 既然用户有“每日脚本”，我们假设本地有就是有。
            return local_data
            
        if not self.yf:
            return {}
        
        try:
            stock = self.yf.Ticker(ticker)
            hist = stock.history(start=start, end=end)
            
            if hist.empty:
                return {}
            
            # Format and Save to DB
            hist.index = hist.index.tz_localize(None)
            save_list = []
            prices = {}
            
            for dt, row in hist.iterrows():
                date_str = dt.strftime('%Y-%m-%d')
                close_price = float(row['Close'])
                if pd.notna(close_price):
                    prices[date_str] = close_price
                    save_list.append((ticker, date_str, close_price))
            
            self.db.save_prices(save_list)
            
            return prices
            
        except Exception as e:
            print(f"Error fetching price range for {ticker}: {e}")
            return {}
            for idx, row in hist.iterrows():
                date_str = idx.strftime('%Y-%m-%d')
                prices[date_str] = row['Close']
            
            return prices
            
        except Exception as e:
            print(f"Error fetching price range for {ticker}: {e}")
            return {}
    
    def _cache_price(self, ticker: str, date_str: str, price: float):
        """缓存价格"""
        with sqlite3.connect(self.CACHE_DB) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO price_cache (ticker, date, price, fetched_at)
                VALUES (?, ?, ?, ?)
            ''', (ticker, date_str, price, datetime.now().isoformat()))
    
    def _get_cached(self, ticker: str, date_str: str) -> Optional[float]:
        """获取缓存的价格"""
        with sqlite3.connect(self.CACHE_DB) as conn:
            cursor = conn.execute('''
                SELECT price, fetched_at FROM price_cache
                WHERE ticker = ? AND date = ?
            ''', (ticker, date_str))
            row = cursor.fetchone()
            
            if row:
                price, fetched_at = row
                # 检查缓存是否过期
                fetched_dt = datetime.fromisoformat(fetched_at)
                if (datetime.now() - fetched_dt).days < self.CACHE_DAYS:
                    return price
            
            return None
    
    def calculate_return(self, ticker: str, buy_date: str) -> Dict:
        """计算从买入到现在的收益"""
        buy_price = self.get_historical_price(ticker, buy_date)
        current_price = self.get_current_price(ticker)
        
        if buy_price is None or current_price is None:
            return {
                'ticker': ticker,
                'buy_date': buy_date,
                'buy_price': None,
                'current_price': None,
                'return_pct': None,
                'error': 'Price not available'
            }
        
        return_pct = ((current_price - buy_price) / buy_price) * 100
        
        return {
            'ticker': ticker,
            'buy_date': buy_date,
            'buy_price': round(buy_price, 2),
            'current_price': round(current_price, 2),
            'return_pct': round(return_pct, 2),
            'return_str': f"+{return_pct:.1f}%" if return_pct >= 0 else f"{return_pct:.1f}%"
        }
    
    def batch_get_returns(self, holdings: List[Dict]) -> List[Dict]:
        """批量获取持仓收益"""
        results = []
        
        for h in holdings:
            ticker = h.get('ticker')
            buy_date = h.get('date') or h.get('buy_date')
            
            if ticker and buy_date:
                result = self.calculate_return(ticker, buy_date)
                result['investor'] = h.get('investor', '')
                result['company'] = h.get('company', '')
                results.append(result)
        
        return results


# 测试代码
if __name__ == '__main__':
    fetcher = PriceFetcher()
    
    print("测试股价获取...")
    
    # 获取当前价格
    tickers = ['AAPL', 'NVDA', 'AVGO']
    for ticker in tickers:
        price = fetcher.get_current_price(ticker)
        print(f"  {ticker}: ${price:.2f}" if price else f"  {ticker}: N/A")
    
    # 计算收益
    print("\n测试收益计算...")
    result = fetcher.calculate_return('NVDA', '2024-01-01')
    print(f"  NVDA 从 2024-01-01 至今:")
    print(f"    买入价: ${result.get('buy_price', 'N/A')}")
    print(f"    当前价: ${result.get('current_price', 'N/A')}")
    print(f"    收益率: {result.get('return_str', 'N/A')}")
