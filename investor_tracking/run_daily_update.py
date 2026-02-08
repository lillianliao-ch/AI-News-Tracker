
import os
import sys
import logging
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

# 设置路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tracker import Database, SEC13FCollector, Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('daily_update.log')
    ]
)
logger = logging.getLogger("DataEngine")

class DataEngine:
    """
    统一数据引擎：负责维护本地数据仓库 (Data Warehouse)
    实现了 '离线优先' 和 '智能增量更新' 策略
    """
    
    def __init__(self):
        self.db = Database()
        self.sec_collector = SEC13FCollector(db=self.db)
        
    def run_daily_sync(self):
        """执行每日同步任务"""
        logger.info("🚀 Starting Daily Data Sync...")
        
        # 1. 同步 13F 机构持仓 (Metadata-First)
        self._sync_holdings()
        
        # 2. 构建股票池 (Universe)
        tickers = self._build_universe()
        logger.info(f"🌌 Universe built: {len(tickers)} unique tickers to sync.")
        
        # 3. 智能增量同步股价
        self._sync_prices(tickers)
        
        logger.info("✅ Daily Sync Completed successfully.")

    def _sync_holdings(self):
        """同步所有关注机构的 13F 持仓"""
        logger.info("📥 Syncing Institutional Holdings (13F)...")
        investors = self.sec_collector.get_investor_list()
        
        for investor in investors:
            try:
                # fetch_holdings 内部已实现：检查最新日期 -> 决定是否下载 -> 存库
                holdings = self.sec_collector.fetch_holdings(investor)
                if holdings:
                    logger.info(f"   - {investor}: {len(holdings)} holdings verified.")
            except Exception as e:
                logger.error(f"   ❌ Error checking {investor}: {e}")

    def _build_universe(self) -> set:
        """构建需要监控的股票池 (Universe)"""
        all_tickers = set()
        
        # A. 添加固定的基准和ETF
        manual_list = ["^GSPC", "ARKK", "ARKW", "NVDA", "BLK", "BRK-B"]
        all_tickers.update(manual_list)
        
        # B. 从本地数据库获取所有机构的 Top 30 重仓股
        # 直接查库，因为 _sync_holdings 已经保证了库是新的
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # 获取每个投资人最新日期的 top 30 持仓
        # 简化逻辑：获取最近一年确实出现过的所有 Ticker，防止漏掉
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        cursor.execute("SELECT DISTINCT ticker FROM holdings WHERE date > ?", (one_year_ago,))
        rows = cursor.fetchall()
        
        count_from_db = 0
        for row in rows:
            ticker = row[0]
            if ticker and isinstance(ticker, str) and len(ticker) < 10: # 过滤异常代码
                all_tickers.add(ticker)
                count_from_db += 1
                
        conn.close()
        logger.info(f"   - Found {len(manual_list)} manual tickers.")
        logger.info(f"   - Found {count_from_db} active tickers from 13F holdings.")
        
        return all_tickers

    def _sync_prices(self, tickers: set):
        """智能批量同步股价 (Anti-Rate-Limit Version)"""
        import time
        logger.info(f"📈 Syncing Market Data for {len(tickers)} tickers...")
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        full_sync_tickers = []
        incremental_tickers = []
        skip_count = 0
        
        # 1. 分类：全量 vs 增量
        logger.info("   🔍 Classifying tickers...")
        today_date = datetime.now().date()
        
        for ticker in tickers:
            cursor.execute("SELECT MAX(date) FROM prices WHERE ticker = ?", (ticker,))
            res = cursor.fetchone()
            last_date_str = res[0]
            
            if not last_date_str:
                full_sync_tickers.append(ticker)
            else:
                last_dt = datetime.strptime(last_date_str, '%Y-%m-%d').date()
                if last_dt < today_date - timedelta(days=1):
                    incremental_tickers.append(ticker)
                else:
                    skip_count += 1
        
        conn.close()
        logger.info(f"   📋 Plan: {len(full_sync_tickers)} Full Sync (5y), {len(incremental_tickers)} Incremental (1mo), {skip_count} Up-to-date.")
        
        # 2. 执行批量下载
        self._batch_download_and_save(full_sync_tickers, period="5y", batch_size=20)
        self._batch_download_and_save(incremental_tickers, period="1mo", batch_size=50)
        
        logger.info("✅ Price Sync Completed.")

    def _batch_download_and_save(self, tickers: list, period: str, batch_size: int):
        """批量下载并保存数据"""
        import time
        if not tickers:
            return

        total = len(tickers)
        for i in range(0, total, batch_size):
            batch = tickers[i : i + batch_size]
            logger.info(f"   🔄 Batch {i//batch_size + 1}/{(total-1)//batch_size + 1}: Fetching {len(batch)} tickers ({period})...")
            
            try:
                # 随机延时防封
                time.sleep(2) 
                
                # yfinance 批量下载
                # group_by='ticker' 让结构变成 {Ticker: DataFrame} 方便处理，但在最新版可能不同
                # 默认是 MultiIndex columns: (Price, Ticker)
                data = yf.download(batch, period=period, group_by='ticker', progress=False, threads=True, ignore_tz=True)
                
                if data.empty:
                    continue
                
                # 保存数据
                success_count = 0
                save_data = []
                
                # 如果 batch 只有一个 ticker，yfinance 返回的不是 MultiIndex (取决于 auto_adjust 参数等)
                # 统一处理：
                if len(batch) == 1:
                    # 单个 ticker 结构
                    ticker = batch[0]
                    # 有时候 yfinance 对于单个 ticker 下载失败会返回空 DF，或者只有 index
                    if 'Close' in data.columns:
                        for dt, row in data.iterrows():
                            if pd.notna(row['Close']):
                                save_data.append((ticker, dt.strftime('%Y-%m-%d'), float(row['Close'])))
                        success_count = 1
                else:
                    # 多个 ticker，结构通常是 data[Ticker]['Close']
                    for ticker in batch:
                        try:
                            # 尝试获取该 ticker 的数据
                            # 如果 data 是 MultiIndex columns (Ticker, Price) 或 (Price, Ticker)
                            # group_by='ticker' -> Data is dict-like or MultiIndex with Ticker at level 0
                            ticker_df = data.get(ticker)
                            
                            if ticker_df is None or ticker_df.empty:
                                continue
                                
                            if 'Close' in ticker_df.columns:
                                # 提取 Close 列
                                series = ticker_df['Close']
                                for dt, val in series.items():
                                    if pd.notna(val):
                                        save_data.append((ticker, dt.strftime('%Y-%m-%d'), float(val)))
                                success_count += 1
                        except Exception as e:
                            # logger.warning(f"Failed parsing {ticker}: {e}")
                            pass
                
                if save_data:
                    self.db.save_prices(save_data)
                    # logger.info(f"      Saved {len(save_data)} records.")
                
            except Exception as e:
                logger.error(f"   ❌ Batch failed: {e}")
                time.sleep(5) # 出错多歇会儿

if __name__ == "__main__":
    engine = DataEngine()
    engine.run_daily_sync()
