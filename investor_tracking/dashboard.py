"""
投资人持仓监控仪表盘
使用 Streamlit 构建的可视化界面
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tracker import (
    Database, ARKCollector, SEC13FCollector, CongressCollector,
    Config, Holding, CongressTrade
)

# ==================== 页面配置 ====================

st.set_page_config(
    page_title="投资人持仓监控",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 数据加载 ====================

@st.cache_resource
def get_collectors():
    """获取数据采集器实例"""
    return {
        'db': Database(),
        'ark': ARKCollector(),
        'sec13f': SEC13FCollector(),
        'congress': CongressCollector()
    }

@st.cache_data(ttl=3600)
def load_ark_holdings():
    """加载 ARK 持仓数据"""
    collectors = get_collectors()
    all_holdings = []
    
    for fund in Config.ARK_FUNDS:
        holdings = collectors['db'].get_latest_holdings(f'ARK_{fund}')
        if holdings:
            for h in holdings:
                all_holdings.append({
                    'Fund': fund,
                    'Ticker': h.ticker,
                    'Company': h.company,
                    'Shares': h.shares,
                    'Value': h.value,
                    'Weight': h.weight,
                    'Date': h.date
                })
    
    return pd.DataFrame(all_holdings)

@st.cache_data(ttl=3600)
def fetch_13f_holdings(investor_name: str):
    """获取 13F 持仓"""
    collectors = get_collectors()
    holdings = collectors['sec13f'].fetch_holdings(investor_name)
    
    if not holdings:
        return pd.DataFrame()
    
    data = []
    for h in holdings:
        data.append({
            'Ticker': h.ticker,
            'Company': h.company,
            'Shares': h.shares,
            'Value': h.value,
            'Weight': h.weight,
            'Date': h.date
        })
    
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def fetch_congress_trades(politician_name: str):
    """获取国会交易"""
    collectors = get_collectors()
    trades = collectors['congress'].fetch_trades(politician_name)
    
    if not trades:
        return pd.DataFrame()
    
    data = []
    for t in trades:
        data.append({
            'Ticker': t.ticker,
            'Company': t.company,
            'Type': t.trade_type.upper(),
            'Date': t.trade_date,
            'Amount': t.amount_range,
            'Owner': t.owner
        })
    
    return pd.DataFrame(data)

# ==================== 侧边栏 ====================

with st.sidebar:
    st.markdown("## 🎯 导航")
    
    page = st.radio(
        "选择页面",
        ["📊 总览", "🚀 ARK 持仓", "💼 13F 持仓", "🏛️ 国会交易", "🔗 交叉信号"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    st.markdown("### ⚙️ 设置")
    auto_refresh = st.checkbox("自动刷新数据", value=False)
    
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    st.markdown("### 📅 数据更新")
    st.caption(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ==================== 页面内容 ====================

if page == "📊 总览":
    st.markdown('<h1 class="main-header">📊 投资人持仓监控</h1>', unsafe_allow_html=True)
    
    # 指标卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("ARK 基金", f"{len(Config.ARK_FUNDS)} 只", "每日更新")
    
    with col2:
        collectors = get_collectors()
        st.metric("13F 投资人", f"{len(collectors['sec13f'].get_investor_list())} 位", "季度更新")
    
    with col3:
        st.metric("国会议员", f"{len(collectors['congress'].get_politician_list())} 位", "交易后 45 天")
    
    with col4:
        ark_df = load_ark_holdings()
        total_stocks = len(ark_df['Ticker'].unique()) if not ark_df.empty else 0
        st.metric("跟踪股票", f"{total_stocks} 只", "持续监控")
    
    st.divider()
    
    # 快速概览
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 ARK 热门持仓")
        ark_df = load_ark_holdings()
        if not ark_df.empty:
            # 按总权重聚合
            top_holdings = ark_df.groupby('Ticker').agg({
                'Company': 'first',
                'Weight': 'sum',
                'Value': 'sum'
            }).sort_values('Weight', ascending=False).head(10).reset_index()
            
            fig = px.bar(
                top_holdings,
                x='Ticker',
                y='Weight',
                color='Weight',
                color_continuous_scale='Viridis',
                title='ARK 基金 Top 10 持仓 (按权重)',
                labels={'Weight': '总权重 (%)'}
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无 ARK 持仓数据，请先运行 `python3 tracker.py check`")
    
    with col2:
        st.markdown("### 🏛️ 最新国会交易")
        pelosi_df = fetch_congress_trades("Nancy Pelosi")
        if not pelosi_df.empty:
            st.dataframe(
                pelosi_df.head(8),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("暂无国会交易数据")

elif page == "🚀 ARK 持仓":
    st.markdown('<h1 class="main-header">🚀 ARK Invest 持仓分析</h1>', unsafe_allow_html=True)
    
    # 基金选择
    selected_fund = st.selectbox(
        "选择基金",
        ["全部"] + Config.ARK_FUNDS
    )
    
    ark_df = load_ark_holdings()
    
    if not ark_df.empty:
        if selected_fund != "全部":
            ark_df = ark_df[ark_df['Fund'] == selected_fund]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("持仓数量", len(ark_df['Ticker'].unique()))
        with col2:
            total_value = ark_df['Value'].sum()
            st.metric("总市值", f"${total_value/1e9:.2f}B")
        with col3:
            st.metric("数据日期", ark_df['Date'].iloc[0] if len(ark_df) > 0 else "N/A")
        
        st.divider()
        
        # 持仓表格
        st.markdown("### 📋 持仓详情")
        
        display_df = ark_df.groupby(['Ticker', 'Company']).agg({
            'Fund': lambda x: ', '.join(sorted(set(x))),
            'Shares': 'sum',
            'Value': 'sum',
            'Weight': 'mean'
        }).reset_index().sort_values('Value', ascending=False)
        
        display_df['Value_Str'] = display_df['Value'].apply(
            lambda x: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K"
        )
        
        st.dataframe(
            display_df[['Ticker', 'Company', 'Fund', 'Shares', 'Value_Str', 'Weight']].rename(
                columns={'Value_Str': 'Value', 'Fund': 'Funds'}
            ),
            use_container_width=True,
            hide_index=True
        )
        
        # 饼图
        st.markdown("### 📊 持仓分布")
        top_10 = display_df.head(10)
        others = display_df.iloc[10:]['Value'].sum()
        
        pie_data = pd.concat([
            top_10[['Ticker', 'Value']],
            pd.DataFrame([{'Ticker': 'Others', 'Value': others}])
        ])
        
        fig = px.pie(
            pie_data,
            values='Value',
            names='Ticker',
            title='持仓分布 (按市值)',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("暂无 ARK 持仓数据，请先运行 `python3 tracker.py check`")

elif page == "💼 13F 持仓":
    st.markdown('<h1 class="main-header">💼 SEC 13F 持仓分析</h1>', unsafe_allow_html=True)
    
    collectors = get_collectors()
    investor_list = collectors['sec13f'].get_investor_list()
    
    selected_investor = st.selectbox(
        "选择投资人",
        investor_list,
        index=0
    )
    
    with st.spinner(f"正在获取 {selected_investor} 的持仓数据..."):
        holdings_df = fetch_13f_holdings(selected_investor)
    
    if not holdings_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("持仓数量", len(holdings_df))
        with col2:
            total_value = holdings_df['Value'].sum()
            st.metric("总市值", f"${total_value/1e9:.2f}B")
        with col3:
            st.metric("披露日期", holdings_df['Date'].iloc[0] if len(holdings_df) > 0 else "N/A")
        
        st.divider()
        
        # Top 20 持仓
        st.markdown("### 📋 Top 20 持仓")
        
        display_df = holdings_df.head(20).copy()
        display_df['Value_Str'] = display_df['Value'].apply(
            lambda x: f"${x/1e9:.2f}B" if x >= 1e9 else f"${x/1e6:.0f}M"
        )
        display_df['Weight_Str'] = display_df['Weight'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            display_df[['Ticker', 'Company', 'Shares', 'Value_Str', 'Weight_Str']].rename(
                columns={'Value_Str': 'Value', 'Weight_Str': 'Weight'}
            ),
            use_container_width=True,
            hide_index=True
        )
        
        # 柱状图
        fig = px.bar(
            display_df.head(15),
            x='Ticker',
            y='Weight',
            color='Value',
            color_continuous_scale='Blues',
            title=f'{selected_investor} Top 15 持仓',
            labels={'Weight': '权重 (%)'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"正在加载 {selected_investor} 的数据...")

elif page == "🏛️ 国会交易":
    st.markdown('<h1 class="main-header">🏛️ 国会议员交易追踪</h1>', unsafe_allow_html=True)
    
    collectors = get_collectors()
    politician_list = collectors['congress'].get_politician_list()
    
    selected_politician = st.selectbox(
        "选择议员",
        politician_list,
        index=0  # Nancy Pelosi
    )
    
    with st.spinner(f"正在获取 {selected_politician} 的交易记录..."):
        trades_df = fetch_congress_trades(selected_politician)
    
    if not trades_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("交易笔数", len(trades_df))
        with col2:
            buy_count = len(trades_df[trades_df['Type'] == 'BUY'])
            st.metric("买入", buy_count)
        with col3:
            sell_count = len(trades_df[trades_df['Type'] == 'SELL'])
            st.metric("卖出", sell_count)
        
        st.divider()
        
        # 交易表格
        st.markdown("### 📋 交易记录")
        
        # 添加颜色标记
        def highlight_type(val):
            if val == 'BUY':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'SELL':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        styled_df = trades_df.style.applymap(
            highlight_type,
            subset=['Type']
        )
        
        st.dataframe(trades_df, use_container_width=True, hide_index=True)
        
        # 股票交易频率
        st.markdown("### 📊 交易股票分布")
        ticker_counts = trades_df['Ticker'].value_counts().head(10)
        
        fig = px.bar(
            x=ticker_counts.index,
            y=ticker_counts.values,
            title=f'{selected_politician} 交易频率 Top 10',
            labels={'x': 'Ticker', 'y': '交易次数'},
            color=ticker_counts.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"暂无 {selected_politician} 的交易数据")

elif page == "🔗 交叉信号":
    st.markdown('<h1 class="main-header">🔗 多源交叉信号分析</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    分析多个投资人/机构共同看好的股票，发现潜在的投资机会。
    """)
    
    # 加载数据
    ark_df = load_ark_holdings()
    pelosi_df = fetch_congress_trades("Nancy Pelosi")
    
    if not ark_df.empty:
        ark_tickers = set(ark_df['Ticker'].unique())
        
        # 尝试获取巴菲特持仓
        buffett_df = fetch_13f_holdings("Berkshire Hathaway")
        buffett_tickers = set(buffett_df['Ticker'].unique()) if not buffett_df.empty else set()
        
        pelosi_tickers = set(pelosi_df['Ticker'].unique()) if not pelosi_df.empty else set()
        
        # 计算交集
        st.markdown("### 🎯 共同持仓分析")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ark_buffett = ark_tickers & buffett_tickers
            st.markdown("#### ARK + 巴菲特")
            if ark_buffett:
                for ticker in list(ark_buffett)[:5]:
                    st.success(f"✅ {ticker}")
            else:
                st.info("暂无共同持仓")
        
        with col2:
            ark_pelosi = ark_tickers & pelosi_tickers
            st.markdown("#### ARK + 佩洛西")
            if ark_pelosi:
                for ticker in list(ark_pelosi)[:5]:
                    st.success(f"✅ {ticker}")
            else:
                st.info("暂无共同持仓")
        
        with col3:
            all_common = ark_tickers & buffett_tickers & pelosi_tickers
            st.markdown("#### 三方共同")
            if all_common:
                for ticker in list(all_common)[:5]:
                    st.warning(f"⭐ {ticker}")
            else:
                st.info("暂无三方共同持仓")
        
        st.divider()
        
        # 特别关注
        st.markdown("### 🌟 特别关注: Tempus AI (TEM)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **为什么值得关注？**
            
            - 🚀 **ARK ARKK** 持仓 ~5%
            - 🏛️ **Nancy Pelosi** 2025-01-14 买入
            - 📈 AI 医疗赛道龙头
            - 💰 2025年营收指引 ~$1.27B
            """)
        
        with col2:
            # TEM 在 ARK 的持仓
            tem_holdings = ark_df[ark_df['Ticker'] == 'TEM']
            if not tem_holdings.empty:
                st.dataframe(
                    tem_holdings[['Fund', 'Weight', 'Value']],
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.warning("请先加载 ARK 持仓数据")

# ==================== 页脚 ====================

st.divider()
st.caption("📊 投资人持仓监控系统 | 数据来源: ARK Invest, SEC EDGAR, Capitol Trades")
