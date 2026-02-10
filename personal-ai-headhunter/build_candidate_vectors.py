#!/usr/bin/env python3
"""
构建候选人向量索引
使用方法: python build_candidate_vectors.py [--force]
"""

import sys
import os

def main():
    force_rebuild = '--force' in sys.argv

    print("🚀 候选人向量索引构建工具")
    print("=" * 60)

    if force_rebuild:
        print("⚠️  强制重建模式")
    else:
        print("📦 智能缓存模式（如索引已存在将直接加载）")

    print()

    from job_search import build_candidate_index

    try:
        index = build_candidate_index(force_rebuild=force_rebuild)

        print()
        print("=" * 60)
        print(f"✅ 成功！候选人向量索引包含 {len(index)} 条记录")
        print()
        print("📊 索引位置: data/candidate_vectors.pkl")
        print("💡 现在可以使用 search_candidates() 进行语义搜索")
        print()

        # 显示几个示例
        if len(index) > 0:
            print("📋 索引示例（前3条）:")
            for i, (cid, data) in enumerate(list(index.items())[:3], 1):
                name = data.get('name', '未知')
                company = data.get('company', '未知公司')
                title = data.get('title', '未知职位')
                print(f"  {i}. {name} - {title} @ {company}")

        print()
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
