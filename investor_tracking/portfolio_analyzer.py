"""
组合分析器 - 计算投资组合的历史收益和风险指标
"""

import os
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass  
class PortfolioMetrics:
    """组合指标"""
    investor: str
    period: str           # 分析周期，如 "3Y"
    total_return: float   # 总收益率
    annual_return: float  # 年化收益率
    max_drawdown: float   # 最大回撤
    volatility: float     # 年化波动率
    sharpe_ratio: float   # 夏普比率
    benchmark_return: float = 0.0  # 基准收益
    alpha: float = 0.0    # 超额收益


class PortfolioAnalyzer:
    """组合分析器 - 收益和风险指标计算"""
    
    # 无风险利率（近似美国国债利率）
    RISK_FREE_RATE = 0.04
    
    # 分析周期
    PERIODS = {
        '1Y': 252,   # 1年约252个交易日
        '2Y': 504,
        '3Y': 756,
        '5Y': 1260,
    }
    
    def __init__(self):
        self.price_fetcher = None
        self._init_price_fetcher()
    
    def _init_price_fetcher(self):
        """初始化价格获取器"""
        try:
            from price_fetcher import PriceFetcher
            self.price_fetcher = PriceFetcher()
        except ImportError:
            print("Warning: price_fetcher module not found")
    
    def calculate_returns(self, prices: np.ndarray) -> np.ndarray:
        """计算日收益率"""
        if len(prices) < 2:
            return np.array([])
        
        returns = np.diff(prices) / prices[:-1]
        return returns
    
    def calculate_total_return(self, prices: np.ndarray) -> float:
        """计算总收益率"""
        if len(prices) < 2:
            return 0.0
        
        return (prices[-1] - prices[0]) / prices[0] * 100
    
    def calculate_annual_return(self, total_return: float, days: int) -> float:
        """计算年化收益率"""
        if days <= 0:
            return 0.0
        
        years = days / 252
        if years <= 0:
            return 0.0
        
        # 年化公式：(1 + total_return)^(1/years) - 1
        return ((1 + total_return / 100) ** (1 / years) - 1) * 100
    
    def calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """计算最大回撤"""
        if len(prices) < 2:
            return 0.0
        
        # 计算累计最大值
        peak = np.maximum.accumulate(prices)
        
        # 计算回撤
        drawdown = (peak - prices) / peak
        
        # 最大回撤
        max_dd = np.max(drawdown) * 100
        
        return max_dd
    
    def calculate_volatility(self, returns: np.ndarray) -> float:
        """计算年化波动率"""
        if len(returns) < 2:
            return 0.0
        
        # 日波动率 * sqrt(252) = 年化波动率
        daily_vol = np.std(returns)
        annual_vol = daily_vol * np.sqrt(252) * 100
        
        return annual_vol
    
    def calculate_sharpe_ratio(self, annual_return: float, volatility: float,
                               risk_free_rate: float = None) -> float:
        """计算夏普比率"""
        if volatility == 0:
            return 0.0
        
        rf = risk_free_rate if risk_free_rate is not None else self.RISK_FREE_RATE
        
        # 夏普比率 = (年化收益 - 无风险收益) / 年化波动率
        sharpe = (annual_return / 100 - rf) / (volatility / 100)
        
        return sharpe
    
    def analyze_portfolio(self, holdings: List[Dict], period: str = '3Y') -> Optional[PortfolioMetrics]:
        """分析投资组合
        
        Args:
            holdings: 持仓列表，每个包含 ticker, weight, date
            period: 分析周期 ('1Y', '2Y', '3Y', '5Y')
        """
        if not holdings or not self.price_fetcher:
            return None
        
        # 模拟组合收益（简化版：等权重）
        returns_list = []
        
        for h in holdings[:20]:  # 限制股票数量
            ticker = h.get('ticker')
            if not ticker:
                continue
            
            try:
                # 获取历史价格
                days = self.PERIODS.get(period, 756)
                end_date = date.today()
                start_date = end_date - timedelta(days=int(days * 1.5))
                
                prices = self.price_fetcher.get_price_range(
                    ticker,
                    start_date.isoformat(),
                    end_date.isoformat()
                )
                
                if prices and len(prices) > 10:
                    price_array = np.array(list(prices.values()))
                    returns = self.calculate_returns(price_array)
                    returns_list.append(returns)
                    
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
                continue
        
        if not returns_list:
            return None
        
        # 计算组合收益（等权重平均）
        min_len = min(len(r) for r in returns_list)
        aligned_returns = [r[-min_len:] for r in returns_list]
        portfolio_returns = np.mean(aligned_returns, axis=0)
        
        # 重建价格序列
        portfolio_prices = np.cumprod(1 + portfolio_returns) * 100
        
        # 计算指标
        total_return = self.calculate_total_return(portfolio_prices)
        annual_return = self.calculate_annual_return(total_return, len(portfolio_returns))
        max_dd = self.calculate_max_drawdown(portfolio_prices)
        volatility = self.calculate_volatility(portfolio_returns)
        sharpe = self.calculate_sharpe_ratio(annual_return, volatility)
        
        return PortfolioMetrics(
            investor=holdings[0].get('investor', 'Unknown'),
            period=period,
            total_return=round(total_return, 2),
            annual_return=round(annual_return, 2),
            max_drawdown=round(max_dd, 2),
            volatility=round(volatility, 2),
            sharpe_ratio=round(sharpe, 2)
        )
    
    def compare_with_benchmark(self, metrics: PortfolioMetrics, 
                               benchmark: str = 'SPY') -> PortfolioMetrics:
        """与基准比较"""
        if not self.price_fetcher:
            return metrics
        
        try:
            days = self.PERIODS.get(metrics.period, 756)
            end_date = date.today()
            start_date = end_date - timedelta(days=int(days * 1.5))
            
            prices = self.price_fetcher.get_price_range(
                benchmark,
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            if prices:
                price_array = np.array(list(prices.values()))
                benchmark_return = self.calculate_total_return(price_array)
                annual_benchmark = self.calculate_annual_return(benchmark_return, len(prices))
                
                metrics.benchmark_return = round(annual_benchmark, 2)
                metrics.alpha = round(metrics.annual_return - annual_benchmark, 2)
                
        except Exception as e:
            print(f"Error comparing with benchmark: {e}")
        
        return metrics
    
    def format_metrics_report(self, metrics: PortfolioMetrics) -> str:
        """格式化指标报告"""
        report = f"""
📊 {metrics.investor} 组合分析 ({metrics.period})
{'='*50}

📈 收益指标
  • 总收益率:   {metrics.total_return:+.2f}%
  • 年化收益:   {metrics.annual_return:+.2f}%
  • 基准收益:   {metrics.benchmark_return:+.2f}% (SPY)
  • Alpha:     {metrics.alpha:+.2f}%

⚠️ 风险指标
  • 最大回撤:   {metrics.max_drawdown:.2f}%
  • 年化波动:   {metrics.volatility:.2f}%
  • 夏普比率:   {metrics.sharpe_ratio:.2f}

💡 解读
{self._interpret_metrics(metrics)}
"""
        return report
    
    def _interpret_metrics(self, m: PortfolioMetrics) -> str:
        """解读指标"""
        interpretations = []
        
        # 夏普比率解读
        if m.sharpe_ratio >= 1.0:
            interpretations.append("  • 夏普比率 > 1：风险调整后收益优秀")
        elif m.sharpe_ratio >= 0.5:
            interpretations.append("  • 夏普比率 0.5-1：风险调整后收益良好")
        else:
            interpretations.append("  • 夏普比率 < 0.5：风险调整后收益一般")
        
        # 最大回撤解读
        if m.max_drawdown <= 15:
            interpretations.append("  • 最大回撤 < 15%：风险控制优秀")
        elif m.max_drawdown <= 30:
            interpretations.append("  • 最大回撤 15-30%：风险控制中等")
        else:
            interpretations.append("  • 最大回撤 > 30%：高风险组合")
        
        # Alpha 解读
        if m.alpha > 5:
            interpretations.append("  • Alpha > 5%：显著跑赢基准")
        elif m.alpha > 0:
            interpretations.append("  • Alpha > 0：小幅跑赢基准")
        else:
            interpretations.append("  • Alpha < 0：跑输基准")
        
        return '\n'.join(interpretations)


# 测试代码
if __name__ == '__main__':
    analyzer = PortfolioAnalyzer()
    
    # 模拟持仓数据
    test_holdings = [
        {'ticker': 'AAPL', 'weight': 0.3, 'investor': 'Test'},
        {'ticker': 'NVDA', 'weight': 0.3, 'investor': 'Test'},
        {'ticker': 'MSFT', 'weight': 0.2, 'investor': 'Test'},
        {'ticker': 'GOOGL', 'weight': 0.2, 'investor': 'Test'},
    ]
    
    print("分析测试组合...")
    print("（注意：Yahoo Finance 有限流，可能需要等待）")
    
    # 由于限流，这里只演示指标计算
    # 使用模拟数据
    prices = np.array([100, 105, 102, 110, 108, 115, 120, 118, 125, 130])
    
    returns = analyzer.calculate_returns(prices)
    total_ret = analyzer.calculate_total_return(prices)
    annual_ret = analyzer.calculate_annual_return(total_ret, len(prices))
    max_dd = analyzer.calculate_max_drawdown(prices)
    vol = analyzer.calculate_volatility(returns)
    sharpe = analyzer.calculate_sharpe_ratio(annual_ret, vol)
    
    print(f"\n模拟数据分析:")
    print(f"  总收益: {total_ret:.2f}%")
    print(f"  最大回撤: {max_dd:.2f}%")
    print(f"  波动率: {vol:.2f}%")
    print(f"  夏普比率: {sharpe:.2f}")
