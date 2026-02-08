"""
LLM 分析器 - 使用 qwen-max 生成智能投资信号解读
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """分析结果"""
    summary: str           # 摘要
    key_signals: str       # 关键信号解读
    sector_trends: str     # 产业趋势
    action_suggestions: str # 建议
    raw_response: str = "" # 原始响应


class LLMAnalyzer:
    """LLM 分析器 - 使用 qwen-max 生成智能解读"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        self.model = 'qwen-max'
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            try:
                import dashscope
                dashscope.api_key = self.api_key
                self.dashscope = dashscope
            except ImportError:
                print("Warning: dashscope not installed. Run: pip install dashscope")
                self.enabled = False
    
    def analyze_signals(self, signals: List[dict]) -> AnalysisResult:
        """分析投资信号并生成解读"""
        if not self.enabled:
            return self._mock_analysis(signals)
        
        # 构建 prompt
        prompt = self._build_analysis_prompt(signals)
        
        try:
            from dashscope import Generation
            
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                result_format='message',
                max_tokens=2000,
                temperature=0.7
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                return self._parse_analysis(content, signals)
            else:
                print(f"LLM Error: {response.code} - {response.message}")
                return self._mock_analysis(signals)
                
        except Exception as e:
            print(f"LLM Analysis Error: {e}")
            return self._mock_analysis(signals)
    
    def _build_analysis_prompt(self, signals: List[dict]) -> str:
        """构建分析 prompt"""
        # 格式化信号数据
        signal_text = ""
        for s in signals[:20]:  # 限制数量
            signal_text += f"- {s.get('level', 'unknown')}: {s.get('ticker', 'N/A')} - {s.get('description', '')}\n"
        
        prompt = f"""你是一位专业的投资分析师。请基于以下投资人持仓变动信号，生成简洁的投资分析报告。

## 今日信号数据
{signal_text}

## 请按以下格式输出分析：

### 📊 摘要
（用 2-3 句话概括今日最重要的发现）

### 🔥 关键信号解读
（解读最重要的 2-3 个信号，包括可能的原因和意义）

### 🏭 产业趋势
（总结观察到的产业或板块趋势）

### 💡 关注建议
（给出 2-3 条值得关注的投资方向，注意：这不构成投资建议）

请用中文回答，保持简洁专业。"""
        
        return prompt
    
    def _parse_analysis(self, content: str, signals: List[dict]) -> AnalysisResult:
        """解析 LLM 响应"""
        # 简单解析，按章节分割
        sections = {
            'summary': '',
            'key_signals': '',
            'sector_trends': '',
            'action_suggestions': ''
        }
        
        current_section = None
        lines = content.split('\n')
        
        for line in lines:
            if '摘要' in line:
                current_section = 'summary'
            elif '关键信号' in line:
                current_section = 'key_signals'
            elif '产业趋势' in line:
                current_section = 'sector_trends'
            elif '关注建议' in line or '建议' in line:
                current_section = 'action_suggestions'
            elif current_section:
                sections[current_section] += line + '\n'
        
        return AnalysisResult(
            summary=sections['summary'].strip(),
            key_signals=sections['key_signals'].strip(),
            sector_trends=sections['sector_trends'].strip(),
            action_suggestions=sections['action_suggestions'].strip(),
            raw_response=content
        )
    
    def _mock_analysis(self, signals: List[dict]) -> AnalysisResult:
        """模拟分析（当 LLM 不可用时）"""
        # 统计信号
        high_signals = [s for s in signals if s.get('level') == 'high']
        
        # 提取关键信息
        tickers = list(set(s.get('ticker', '') for s in high_signals if s.get('ticker')))
        
        summary = f"今日检测到 {len(signals)} 个投资信号"
        if high_signals:
            summary += f"，其中 {len(high_signals)} 个高优先级信号"
        
        key_signals = ""
        for s in high_signals[:3]:
            key_signals += f"• {s.get('description', '')}\n"
        
        sector_trends = "• 需要配置 DASHSCOPE_API_KEY 以获取 AI 分析"
        
        return AnalysisResult(
            summary=summary,
            key_signals=key_signals or "无高优先级信号",
            sector_trends=sector_trends,
            action_suggestions="配置 LLM API 后可获得智能分析建议",
            raw_response=""
        )
    
    def generate_daily_report(self, signals: List[dict], prices: Dict = None) -> str:
        """生成每日报告"""
        analysis = self.analyze_signals(signals)
        
        report = f"""
📊 每日投资信号报告
{'='*50}

{analysis.summary}

🔥 关键信号解读
{'-'*30}
{analysis.key_signals}

🏭 产业趋势
{'-'*30}
{analysis.sector_trends}

💡 关注建议
{'-'*30}
{analysis.action_suggestions}

{'='*50}
⚠️ 以上分析仅供参考，不构成投资建议
"""
        return report


# 测试代码
if __name__ == '__main__':
    analyzer = LLMAnalyzer()
    
    # 模拟信号数据
    test_signals = [
        {'level': 'high', 'ticker': 'AVGO', 'description': 'ARK_ARKK 首次建仓 AVGO'},
        {'level': 'high', 'ticker': 'AVGO', 'description': '共识信号：ARK_ARKW, ARK_ARKK 同时买入 AVGO'},
        {'level': 'medium', 'ticker': 'NVDA', 'description': 'ARK_ARKK 大幅加仓 NVDA (+45%)'},
        {'level': 'medium', 'ticker': 'AI/半导体', 'description': '产业趋势：AI/半导体 整体加仓'},
    ]
    
    print("生成每日报告...")
    report = analyzer.generate_daily_report(test_signals)
    print(report)
