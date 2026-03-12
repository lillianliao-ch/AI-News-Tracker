#!/usr/bin/env python3
"""
批次管理系统 - 完整保存每次运行的所有数据

每次运行创建独立的批次目录，保存：
1. Seed 文件
2. 中间输出（GitHub数据、网站数据等）
3. 最终结果
4. 批次总结报告
"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class BatchManager:
    """批次管理器"""

    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent / "github_mining" / "data" / "batches"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_batch(self, batch_type: str, seeds_file: str, metadata: Dict[str, Any] = None) -> 'BatchSession':
        """
        创建一个新的批次会话

        Args:
            batch_type: 批次类型（如 "phase5_expansion", "phase4_5_enrichment"）
            seeds_file: 种子文件路径
            metadata: 批次元数据

        Returns:
            BatchSession: 批次会话对象
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_dir = self.base_dir / f"{batch_type}_{timestamp}"
        batch_dir.mkdir(parents=True, exist_ok=True)

        # 保存种子文件
        seeds_path = batch_dir / "seeds"
        seeds_path.mkdir(exist_ok=True)
        seeds_dest = seeds_path / f"seeds_{timestamp}.json"
        shutil.copy2(seeds_file, seeds_dest)

        # 创建输出目录
        outputs_dir = batch_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)

        # 创建中间文件目录
        intermediates_dir = batch_dir / "intermediates"
        intermediates_dir.mkdir(exist_ok=True)

        # 初始化批次信息
        batch_info = {
            'batch_id': f"{batch_type}_{timestamp}",
            'batch_type': batch_type,
            'timestamp': timestamp,
            'start_time': datetime.now().isoformat(),
            'seeds_file': str(seeds_file),
            'seeds_count': len(json.load(open(seeds_file))) if Path(seeds_file).exists() else 0,
            'seeds_saved': str(seeds_dest),
            'batch_dir': str(batch_dir),
            'status': 'running',
            **(metadata or {})
        }

        # 保存批次信息
        info_file = batch_dir / "batch_info.json"
        with open(info_file, 'w') as f:
            json.dump(batch_info, f, indent=2)

        return BatchSession(batch_dir, batch_info)

    def get_batch(self, batch_id: str) -> Optional['BatchSession']:
        """获取已存在的批次"""
        batch_dir = self.base_dir / batch_id
        if not batch_dir.exists():
            return None

        info_file = batch_dir / "batch_info.json"
        if not info_file.exists():
            return None

        with open(info_file) as f:
            batch_info = json.load(f)

        return BatchSession(batch_dir, batch_info)

    def list_batches(self, batch_type: str = None, limit: int = 10) -> list:
        """列出批次"""
        batches = []
        for batch_dir in sorted(self.base_dir.glob("*"), reverse=True):
            if not batch_dir.is_dir():
                continue

            if batch_type and not batch_dir.name.startswith(batch_type):
                continue

            info_file = batch_dir / "batch_info.json"
            if info_file.exists():
                with open(info_file) as f:
                    info = json.load(f)
                batches.append(info)

            if len(batches) >= limit:
                break

        return batches


class BatchSession:
    """批次会话 - 管理单个批次的所有数据"""

    def __init__(self, batch_dir: Path, batch_info: Dict[str, Any]):
        self.batch_dir = batch_dir
        self.info = batch_info
        self.outputs_dir = batch_dir / "outputs"
        self.intermediates_dir = batch_dir / "intermediates"
        self.plots_dir = batch_dir / "plots"
        self.plots_dir.mkdir(exist_ok=True)

    def save_output(self, data: Any, filename: str, metadata: Dict = None):
        """保存输出文件"""
        output_path = self.outputs_dir / filename

        if isinstance(data, (list, dict)):
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            shutil.copy2(data, output_path)

        # 记录文件信息
        self._log_file('outputs', filename, output_path, metadata)

        return output_path

    def save_intermediate(self, data: Any, filename: str, metadata: Dict = None):
        """保存中间文件"""
        intermediate_path = self.intermediates_dir / filename

        if isinstance(data, (list, dict)):
            with open(intermediate_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            shutil.copy2(data, intermediate_path)

        # 记录文件信息
        self._log_file('intermediates', filename, intermediate_path, metadata)

        return intermediate_path

    def add_summary(self, summary_data: Dict[str, Any]):
        """添加批次总结"""
        summary_file = self.batch_dir / "summary.json"

        # 合并现有信息
        summary = {
            'batch_id': self.info['batch_id'],
            'timestamp': self.info['timestamp'],
            'start_time': self.info['start_time'],
            'end_time': datetime.now().isoformat(),
            'status': 'completed',
            **summary_data
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # 更新批次信息
        self.info['status'] = 'completed'
        self.info['end_time'] = summary['end_time']
        self.info['summary'] = summary_data
        self._save_info()

        return summary_file

    def add_plot(self, plot_file: str, plot_name: str):
        """添加图表"""
        dest = self.plots_dir / plot_name
        shutil.copy2(plot_file, dest)
        return dest

    def _log_file(self, file_type: str, filename: str, filepath: Path, metadata: Dict = None):
        """记录文件信息"""
        log_file = self.batch_dir / f"{file_type}_log.json"

        logs = []
        if log_file.exists():
            with open(log_file) as f:
                logs = json.load(f)

        log_entry = {
            'filename': filename,
            'path': str(filepath),
            'timestamp': datetime.now().isoformat(),
            'size': filepath.stat().st_size if filepath.exists() else 0
        }

        if metadata:
            log_entry['metadata'] = metadata

        logs.append(log_entry)

        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def _save_info(self):
        """保存批次信息"""
        info_file = self.batch_dir / "batch_info.json"
        with open(info_file, 'w') as f:
            json.dump(self.info, f, indent=2, ensure_ascii=False)

    def get_path(self, subpath: str = ""):
        """获取批次目录路径"""
        if subpath:
            return self.batch_dir / subpath
        return self.batch_dir


# 全局批次管理器实例
_batch_manager = None

def get_batch_manager():
    """获取批次管理器单例"""
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = BatchManager()
    return _batch_manager


if __name__ == "__main__":
    # 测试
    manager = get_batch_manager()
    print(f"📦 批次目录: {manager.base_dir}")
    print(f"\n最近批次:")
    batches = manager.list_batches(limit=5)
    for batch in batches:
        print(f"  - {batch['batch_id']}: {batch.get('status', 'unknown')} ({batch.get('seeds_count', 0)} seeds)")
