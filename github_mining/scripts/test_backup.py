#!/usr/bin/env python3
"""
测试 batch_runner.py 的自动备份功能

测试场景：
1. 创建一个测试批次
2. 运行 phase3 两次，验证第二次会自动备份第一次的输出
3. 检查备份文件是否存在
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# 添加 scripts 目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from batch_runner import safe_backup_if_exists, RUNS_DIR

def test_backup_mechanism():
    print("\n" + "="*60)
    print("🧪 测试自动备份机制")
    print("="*60)

    # 1. 创建测试目录
    test_dir = RUNS_DIR / "test_backup_20260311"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "outputs").mkdir(exist_ok=True)

    test_file = test_dir / "outputs" / "phase3_enriched.json"

    print(f"\n📁 测试目录: {test_dir}")
    print(f"📄 测试文件: {test_file.name}")

    # 2. 第一次写入
    print("\n--- 第一次写入 ---")
    data_v1 = [{"username": "user1", "version": 1}]
    with open(test_file, "w") as f:
        json.dump(data_v1, f, indent=2)
    print(f"✅ 写入版本 1: {test_file}")
    time.sleep(1)  # 确保时间戳不同

    # 3. 第二次写入前备份
    print("\n--- 第二次写入（应该触发备份）---")
    backed_up = safe_backup_if_exists(test_file)

    if backed_up:
        print(f"✅ 自动备份成功")
    else:
        print(f"❌ 备份失败：文件不存在")
        return False

    # 写入新版本
    data_v2 = [{"username": "user2", "version": 2}]
    with open(test_file, "w") as f:
        json.dump(data_v2, f, indent=2)
    print(f"✅ 写入版本 2: {test_file}")
    time.sleep(1)

    # 4. 第三次写入前备份
    print("\n--- 第三次写入（应该再次触发备份）---")
    backed_up = safe_backup_if_exists(test_file)

    if backed_up:
        print(f"✅ 自动备份成功")
    else:
        print(f"❌ 备份失败")
        return False

    # 写入新版本
    data_v3 = [{"username": "user3", "version": 3}]
    with open(test_file, "w") as f:
        json.dump(data_v3, f, indent=2)
    print(f"✅ 写入版本 3: {test_file}")

    # 5. 验证结果
    print("\n" + "="*60)
    print("📊 验证结果")
    print("="*60)

    outputs_dir = test_dir / "outputs"
    all_files = sorted(outputs_dir.glob("phase3_enriched*.json"))

    print(f"\n📂 输出目录中的文件:")
    for f in all_files:
        size = f.stat().st_size
        with open(f) as fp:
            data = json.load(fp)
        version = data[0].get("version", "?")
        print(f"  - {f.name:40s} ({size:3d} bytes, version={version})")

    # 检查
    current_file = outputs_dir / "phase3_enriched.json"
    backup_files = [f for f in all_files if "backup" in f.name]

    print(f"\n✅ 当前文件: {current_file.name}")
    print(f"✅ 备份文件数: {len(backup_files)}")

    if len(backup_files) >= 2:
        print("\n🎉 测试通过！自动备份机制工作正常")
        print(f"   - 当前文件保存了最新版本（version 3）")
        print(f"   - 生成了 {len(backup_files)} 个备份文件")
        return True
    else:
        print("\n❌ 测试失败：备份文件数量不足")
        return False

if __name__ == "__main__":
    success = test_backup_mechanism()
    sys.exit(0 if success else 1)
