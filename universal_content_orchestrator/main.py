import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.sources.opencli_hackernews import OpenCLIHackerNewsSource
from src.sources.legacy_rss import LegacyRSSSource
from src.core.llm_engine import QwenEngine
from src.core.visual_engine import PillowVisualEngine
from src.publishers.opencli_xhs_adapter import OpenCLIXiaohongshuPublisher
from src.publishers.telegram_adapter import TelegramPublisher
from src.publishers.wechat_adapter import WeChatPublisher
from src.core.state_manager import EventStateManager

def process_single_event(event, brain, visual, xhs, wechat, state_manager):
    draft = brain.synthesize_single_article(event)
    draft = draft.replace("\\n", "\n")
    lines = [l.strip() for l in draft.split('\n') if l.strip()]
    raw_title = lines[0] if lines else "AI行业新风向"
    raw_sub = lines[1] if len(lines) > 1 else "技术底座洗牌"
    
    title = raw_title.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").strip()
    subtitle = raw_sub.replace("【", "").replace("】", "").replace("[", "").replace("]", "").replace("*", "").strip()
    
    if len(title) > 19: title = title[:18] + "…"
    if len(subtitle) > 40: subtitle = subtitle[:38] + "..."
    
    poster_path_xhs = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"poster_xhs_{event.id}.jpg")
    poster_path_wx = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"poster_wx_{event.id}.jpg")
    
    visual.generate_poster(title=title, subtitle=subtitle, badge="Lilian甄选", output_path=poster_path_xhs, mode="xhs")
    visual.generate_poster(title=title, subtitle=subtitle, badge="Lilian甄选", output_path=poster_path_wx, mode="wechat")
    
    print(f"🖼️ [分发准备] 双端海报集群生成完毕")
    
    success_xhs = xhs.push(content=draft, title=title, media_paths=[poster_path_xhs])
    success_wx = wechat.push(title=title, content_md=draft, poster_path=poster_path_wx)
    
    if success_xhs or success_wx:
        print(f"✅ 成功投递全域矩阵: {title}")
        state_manager.mark_success(event)
    else:
        print(f"⚠️ 投递失败警告: {title} (环境脱机)")
        
    return {"title": title, "success": success_xhs or success_wx}

def main():
    print("==========================================================================")
    print("🌟 启动 Lilian 1-to-1 Content Factory 裂变引擎 🌟")
    print("==========================================================================\n")
    
    # 注入数据池（刻意抓大一点的数字，让 LLM 做淘汰赛）
    hn_source = OpenCLIHackerNewsSource()
    rss_source = LegacyRSSSource({
        "36Kr_AI": "https://36kr.com/feed", 
        "QbitAI": "https://www.qbitai.com/feed",
        "InfoQ": "https://www.infoq.cn/feed",
        "TechCrunch": "https://techcrunch.com/category/artificial-intelligence/feed/"
    })
    
    print("📡 [1] 开始从全球口径超量捕获候投资讯池...")
    # Fetch buffers (limit ignored in fetch, we process internally)
    hn_pool = hn_source.fetch(limit=15)
    rss_pool = rss_source.fetch(limit=25) 
    
    brain = QwenEngine()
    visual = PillowVisualEngine()
    xhs = OpenCLIXiaohongshuPublisher()
    wechat = WeChatPublisher()
    state_manager = EventStateManager()
    
    print("\n🛡️ [1.5] 记忆海马体介入，拦截库内重复与已发布资讯...")
    new_hn_pool = [e for e in hn_pool if not state_manager.is_processed(e)]
    new_rss_pool = [e for e in rss_pool if not state_manager.is_processed(e)]
    
    hn_dup = len(hn_pool) - len(new_hn_pool)
    rss_dup = len(rss_pool) - len(new_rss_pool)
    print(f"    - HackerNews: 剔除发过历史 {hn_dup} 篇，余 {len(new_hn_pool)} 篇进入海选。")
    print(f"    - RSS News  : 剔除发过历史 {rss_dup} 篇，余 {len(new_rss_pool)} 篇进入海选。")
    
    if not new_hn_pool and not new_rss_pool:
        print("📭 今日暂无待处理全新情报，守护进程休眠。")
        return

    print("\n🧠 [2] 激活主编鉴赏筛选...")
    top_hn = brain.select_top_articles(new_hn_pool, limit=3)
    top_rss = brain.select_top_articles(new_rss_pool, limit=5)
    
    final_events = top_hn + top_rss
    print(f"\n🚀 [3] 淘汰赛结束！选定 {len(final_events)} 篇顶级情报，开始裂变发布流水线：")
    
    results = []
    for i, event in enumerate(final_events, 1):
        print(f"\n[任务 {i}/{len(final_events)}] ==========================")
        res = process_single_event(event, brain, visual, xhs, wechat, state_manager)
        results.append(res)
        
    print("\n📩 [4] 启动 Telegram 全局移动端通报矩阵...")
    tg = TelegramPublisher()
    tg.push_summary(results)
        
    print("\n✅ 所有批次发布与推送循环已绝美完结！")
    
if __name__ == "__main__":
    main()
