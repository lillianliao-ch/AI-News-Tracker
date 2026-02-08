"""
信号检测模块 - 分析持仓变动并生成分级信号
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime, date
from enum import Enum


class SignalLevel(Enum):
    """信号优先级"""
    HIGH = "high"      # 🔴 高优先级：多人共同买入、首次建仓、清仓
    MEDIUM = "medium"  # 🟡 中优先级：大幅加仓、产业趋势
    LOW = "low"        # 🟢 低优先级：小幅变动


class SignalType(Enum):
    """信号类型"""
    # 高优先级
    MULTI_INVESTOR_BUY = "multi_investor_buy"    # 多个投资人同时买入
    NEW_POSITION = "new_position"                # 首次建仓
    EXIT_POSITION = "exit_position"              # 完全清仓
    
    # 中优先级  
    LARGE_INCREASE = "large_increase"            # 大幅加仓 (>50%)
    LARGE_DECREASE = "large_decrease"            # 大幅减仓 (>50%)
    SECTOR_TREND = "sector_trend"                # 产业趋势
    
    # 低优先级
    SMALL_INCREASE = "small_increase"            # 小幅加仓
    SMALL_DECREASE = "small_decrease"            # 小幅减仓


@dataclass
class Signal:
    """投资信号"""
    level: SignalLevel
    type: SignalType
    ticker: str
    company: str
    investors: List[str]        # 相关投资人
    description: str            # 信号描述
    change_pct: float = 0.0     # 变动百分比
    value: float = 0.0          # 涉及金额
    date: str = ""              # 信号日期
    metadata: Dict = field(default_factory=dict)  # 额外信息

    def __post_init__(self):
        if not self.date:
            self.date = date.today().isoformat()

    @property
    def emoji(self) -> str:
        """获取信号对应的 emoji"""
        emoji_map = {
            SignalType.MULTI_INVESTOR_BUY: "🔥",
            SignalType.NEW_POSITION: "🆕",
            SignalType.EXIT_POSITION: "🚨",
            SignalType.LARGE_INCREASE: "📈",
            SignalType.LARGE_DECREASE: "📉",
            SignalType.SECTOR_TREND: "🏭",
            SignalType.SMALL_INCREASE: "➕",
            SignalType.SMALL_DECREASE: "➖",
        }
        return emoji_map.get(self.type, "•")

    @property
    def level_emoji(self) -> str:
        """优先级 emoji"""
        return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(self.level.value, "⚪")


class SignalDetector:
    """信号检测器 - 分析持仓变动并生成分级信号"""
    
    # 阈值配置
    LARGE_CHANGE_THRESHOLD = 0.5   # 50% 以上为大幅变动
    SMALL_CHANGE_THRESHOLD = 0.1   # 10% 以下为小幅变动
    
    # 产业分类
    SECTOR_MAP = {
        # AI & 科技
        'NVDA': 'AI/半导体', 'AMD': 'AI/半导体', 'AVGO': 'AI/半导体',
        'MSFT': 'AI/云计算', 'GOOGL': 'AI/云计算', 'AMZN': 'AI/云计算',
        'META': 'AI/社交', 'AAPL': '消费科技',
        # AI 应用
        'TEM': 'AI/医疗', 'TSLA': 'AI/自动驾驶', 'PLTR': 'AI/数据',
        # 金融
        'JPM': '金融', 'BAC': '金融', 'WFC': '金融', 'GS': '金融',
        'V': '金融科技', 'MA': '金融科技', 'COIN': '加密货币',
        # 能源
        'XOM': '能源', 'CVX': '能源', 'OXY': '能源',
        # 医疗
        'UNH': '医疗', 'JNJ': '医疗', 'PFE': '医疗',
        # 消费
        'KO': '消费', 'PEP': '消费', 'PG': '消费',
    }
    
    def __init__(self):
        self.signals: List[Signal] = []
    
    def detect_from_changes(self, changes: List[dict], investor: str) -> List[Signal]:
        """从持仓变动中检测信号"""
        signals = []
        
        for change in changes:
            ticker = change.get('ticker', '')
            action = change.get('action', '')
            change_pct = change.get('change_pct', 0)
            company = change.get('company', '')
            
            signal = self._classify_change(
                ticker=ticker,
                company=company,
                action=action,
                change_pct=change_pct,
                investor=investor
            )
            
            if signal:
                signals.append(signal)
        
        return signals
    
    def _classify_change(self, ticker: str, company: str, action: str, 
                         change_pct: float, investor: str) -> Optional[Signal]:
        """将变动分类为信号"""
        
        # 新建仓 - 高优先级
        if action == 'NEW':
            return Signal(
                level=SignalLevel.HIGH,
                type=SignalType.NEW_POSITION,
                ticker=ticker,
                company=company,
                investors=[investor],
                description=f"{investor} 首次建仓 {ticker}",
                change_pct=change_pct
            )
        
        # 清仓 - 高优先级
        if action == 'EXIT':
            return Signal(
                level=SignalLevel.HIGH,
                type=SignalType.EXIT_POSITION,
                ticker=ticker,
                company=company,
                investors=[investor],
                description=f"{investor} 完全清仓 {ticker}",
                change_pct=-100
            )
        
        # 大幅加仓 - 中优先级
        if action == 'ADD' and abs(change_pct) >= self.LARGE_CHANGE_THRESHOLD * 100:
            return Signal(
                level=SignalLevel.MEDIUM,
                type=SignalType.LARGE_INCREASE,
                ticker=ticker,
                company=company,
                investors=[investor],
                description=f"{investor} 大幅加仓 {ticker} (+{change_pct:.1f}%)",
                change_pct=change_pct
            )
        
        # 大幅减仓 - 中优先级
        if action == 'REDUCE' and abs(change_pct) >= self.LARGE_CHANGE_THRESHOLD * 100:
            return Signal(
                level=SignalLevel.MEDIUM,
                type=SignalType.LARGE_DECREASE,
                ticker=ticker,
                company=company,
                investors=[investor],
                description=f"{investor} 大幅减仓 {ticker} ({change_pct:.1f}%)",
                change_pct=change_pct
            )
        
        # 小幅变动 - 低优先级
        if action == 'ADD':
            return Signal(
                level=SignalLevel.LOW,
                type=SignalType.SMALL_INCREASE,
                ticker=ticker,
                company=company,
                investors=[investor],
                description=f"{investor} 小幅加仓 {ticker} (+{change_pct:.1f}%)",
                change_pct=change_pct
            )
        
        if action == 'REDUCE':
            return Signal(
                level=SignalLevel.LOW,
                type=SignalType.SMALL_DECREASE,
                ticker=ticker,
                company=company,
                investors=[investor],
                description=f"{investor} 小幅减仓 {ticker} ({change_pct:.1f}%)",
                change_pct=change_pct
            )
        
        return None
    
    def detect_multi_investor_signals(self, all_signals: List[Signal]) -> List[Signal]:
        """检测多投资人共同信号"""
        # 按股票分组
        ticker_signals: Dict[str, List[Signal]] = {}
        
        for signal in all_signals:
            if signal.type in [SignalType.NEW_POSITION, SignalType.LARGE_INCREASE]:
                if signal.ticker not in ticker_signals:
                    ticker_signals[signal.ticker] = []
                ticker_signals[signal.ticker].append(signal)
        
        # 找出被多人买入的股票
        multi_signals = []
        for ticker, signals in ticker_signals.items():
            investors = list(set(s.investors[0] for s in signals))
            if len(investors) >= 2:
                multi_signals.append(Signal(
                    level=SignalLevel.HIGH,
                    type=SignalType.MULTI_INVESTOR_BUY,
                    ticker=ticker,
                    company=signals[0].company,
                    investors=investors,
                    description=f"🔥 共识信号：{', '.join(investors)} 同时买入 {ticker}",
                    metadata={'individual_signals': signals}
                ))
        
        return multi_signals
    
    def detect_sector_trends(self, all_signals: List[Signal]) -> List[Signal]:
        """检测产业趋势"""
        # 按产业分组统计买入/卖出
        sector_changes: Dict[str, Dict] = {}
        
        for signal in all_signals:
            sector = self.SECTOR_MAP.get(signal.ticker, '其他')
            if sector not in sector_changes:
                sector_changes[sector] = {'buy': 0, 'sell': 0, 'tickers': []}
            
            if signal.type in [SignalType.NEW_POSITION, SignalType.LARGE_INCREASE, SignalType.SMALL_INCREASE]:
                sector_changes[sector]['buy'] += 1
                sector_changes[sector]['tickers'].append(signal.ticker)
            elif signal.type in [SignalType.EXIT_POSITION, SignalType.LARGE_DECREASE, SignalType.SMALL_DECREASE]:
                sector_changes[sector]['sell'] += 1
        
        # 生成产业趋势信号
        trend_signals = []
        for sector, data in sector_changes.items():
            if sector == '其他':
                continue
            
            net = data['buy'] - data['sell']
            if abs(net) >= 2:  # 至少 2 个净变动
                trend_type = "加仓" if net > 0 else "减仓"
                trend_signals.append(Signal(
                    level=SignalLevel.MEDIUM,
                    type=SignalType.SECTOR_TREND,
                    ticker=sector,
                    company=sector,
                    investors=[],
                    description=f"产业趋势：{sector} 整体{trend_type} ({data['buy']}买/{data['sell']}卖)",
                    metadata={'tickers': list(set(data['tickers']))}
                ))
        
        return trend_signals
    
    def format_signals_for_telegram(self, signals: List[Signal]) -> str:
        """格式化信号为 Telegram 消息"""
        if not signals:
            return "📊 今日无重要信号"
        
        # 按优先级分组
        high = [s for s in signals if s.level == SignalLevel.HIGH]
        medium = [s for s in signals if s.level == SignalLevel.MEDIUM]
        low = [s for s in signals if s.level == SignalLevel.LOW]
        
        lines = [f"📊 *每日投资信号* ({date.today()})\n"]
        
        if high:
            lines.append("🔴 *高优先级信号*")
            for s in high[:5]:
                lines.append(f"  {s.emoji} `{s.ticker}` {s.description}")
            lines.append("")
        
        if medium:
            lines.append("🟡 *中优先级信号*")
            for s in medium[:5]:
                lines.append(f"  {s.emoji} `{s.ticker}` {s.description}")
            lines.append("")
        
        if low and len(high) + len(medium) < 5:
            lines.append("🟢 *其他变动*")
            for s in low[:3]:
                lines.append(f"  {s.emoji} `{s.ticker}` {s.description}")
        
        lines.append(f"\n_共 {len(signals)} 个信号_")
        
        return "\n".join(lines)


# 测试代码
if __name__ == '__main__':
    detector = SignalDetector()
    
    # 模拟变动数据
    test_changes = [
        {'ticker': 'NVDA', 'company': 'NVIDIA', 'action': 'ADD', 'change_pct': 60},
        {'ticker': 'TEM', 'company': 'Tempus AI', 'action': 'NEW', 'change_pct': 100},
        {'ticker': 'AAPL', 'company': 'Apple', 'action': 'REDUCE', 'change_pct': -30},
    ]
    
    signals = detector.detect_from_changes(test_changes, 'ARK_ARKK')
    
    print("检测到的信号：")
    for s in signals:
        print(f"  {s.level_emoji} {s.emoji} {s.description}")
    
    print("\nTelegram 格式：")
    print(detector.format_signals_for_telegram(signals))
