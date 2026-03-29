import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from universal_content_orchestrator.src.core.visual_engine import PillowVisualEngine

vc = PillowVisualEngine()
vc.generate_poster(
    title="首发 | 中国量子计算的GPT时刻",
    subtitle="这不是概念路演，是双平台实测数据反推的时间锚点。王兴兴定义的“GPT时刻”本质是多模态闭环鲁棒性阈值。",
    badge="Lilian甄选",
    output_path="/tmp/wx_poster_test.jpg",
    mode="wechat"
)
