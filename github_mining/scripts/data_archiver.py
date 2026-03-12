#!/usr/bin/env python3
"""
数据归档系统 - 防止历史数据被覆盖

每次运行后自动归档到带时间戳的目录
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
import json


class DataArchiver:
    """数据归档器"""

    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent / "github_mining"
        self.archive_dir = self.base_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)

    def archive_run(self, source_file, run_type, seeds_name, metadata=None):
        """
        归档一次运行的数据

        Args:
            source_file: 源文件路径
            run_type: 运行类型（如 "phase5_expanded"）
            seeds_name: 种子文件名（如 "phase4_round2_seeds_0308"）
            metadata: 额外元数据（字典）
        """
        source = Path(source_file)
        if not source.exists():
            print(f"⚠️  源文件不存在: {source}")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建归档目录结构：archive/run_type/YYYYMM/
        archive_path = self.archive_dir / run_type / datetime.now().strftime('%Y%m')
        archive_path.mkdir(parents=True, exist_ok=True)

        # 归档文件名：run_type_seeds_name_timestamp.json
        archive_filename = f"{run_type}_{seeds_name}_{timestamp}.json"
        archive_file = archive_path / archive_filename

        # 复制文件
        shutil.copy2(source, archive_file)

        # 保存元数据
        if metadata:
            meta_file = archive_path / f"{archive_filename}.meta.json"
            with open(meta_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'source_file': str(source),
                    'run_type': run_type,
                    'seeds_name': seeds_name,
                    **metadata
                }, f, indent=2)

        # 更新索引
        self._update_index(run_type, {
            'timestamp': timestamp,
            'archive_file': str(archive_file),
            'seeds_name': seeds_name,
            'size': archive_file.stat().st_size,
            **metadata
        })

        print(f"📦 已归档: {archive_file.name}")
        print(f"   位置: {archive_file}")
        return archive_file

    def _update_index(self, run_type, entry):
        """更新归档索引"""
        index_file = self.archive_dir / f"{run_type}_index.json"
        index = []
        if index_file.exists():
            with open(index_file) as f:
                index = json.load(f)
        index.append(entry)
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)

    def list_archives(self, run_type=None):
        """列出所有归档"""
        if run_type:
            index_file = self.archive_dir / f"{run_type}_index.json"
            if index_file.exists():
                with open(index_file) as f:
                    return json.load(f)
        else:
            # 列出所有归档文件
            archives = []
            for idx_file in self.archive_dir.glob("*_index.json"):
                with open(idx_file) as f:
                    archives.extend(json.load(f))
            return archives

    def restore_archive(self, archive_file, target_path):
        """恢复归档文件"""
        archive = Path(archive_file)
        target = Path(target_path)
        shutil.copy2(archive, target)
        print(f"✅ 已恢复: {target}")
        return target


if __name__ == "__main__":
    # 测试
    archiver = DataArchiver()
    print(f"📦 归档目录: {archiver.archive_dir}")
    print(f"\n现有归档:")
    for run_type in ["phase5_expanded", "phase4_expanded"]:
        archives = archiver.list_archives(run_type)
        if archives:
            print(f"\n{run_type}:")
            for arch in archives[-5:]:  # 最近5个
                print(f"  - {arch.get('timestamp')}: {arch.get('seeds_name')}")
