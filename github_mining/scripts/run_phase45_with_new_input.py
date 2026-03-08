#!/usr/bin/env python3
"""
Phase 4.5: LLM 深度富化 - 使用 Phase 3.5 最新输出

这个脚本使用刚生成的 phase4_final_enriched.json (11,976 人)
而不是旧的 phase3_5_enriched.json (3,723 人)
"""

import os
import sys
from pathlib import Path

# 添加 scripts 目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# 临时修改 Phase 4.5 的输入文件路径
import run_phase4_5_llm_enrichment as phase45_module

# 修改 INPUT_FILE 为新文件
original_input = phase45_module.INPUT_FILE
new_input = script_dir / "github_mining" / "phase4_final_enriched.json"

if new_input.exists():
    print(f"🔄 更新 Phase 4.5 输入文件:")
    print(f"   旧文件: {original_input}")
    print(f"   新文件: {new_input}")
    phase45_module.INPUT_FILE = new_input

    # 运行 Phase 4.5
    print(f"\n🚀 启动 Phase 4.5...")
    phase45_module.main()
else:
    print(f"❌ 错误: 新输入文件不存在: {new_input}")
    sys.exit(1)
