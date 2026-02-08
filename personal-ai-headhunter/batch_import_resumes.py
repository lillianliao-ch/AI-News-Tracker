#!/usr/bin/env python3
"""
批量导入简历到后台处理队列
用法: python batch_import_resumes.py <目录路径>
"""

import os
import sys
import shutil
import uuid
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, ResumeTask

# 配置
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.docx', '.jpg', '.jpeg', '.png', '.webp']


def batch_import(source_dir: str, skip_existing: bool = True):
    """
    批量导入某目录下的所有简历到处理队列
    
    Args:
        source_dir: 源目录路径
        skip_existing: 是否跳过已存在的文件（基于文件名）
    """
    if not os.path.isdir(source_dir):
        print(f"❌ 目录不存在: {source_dir}")
        return
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    db = SessionLocal()
    
    # 获取所有支持的文件
    files = []
    for f in os.listdir(source_dir):
        ext = os.path.splitext(f)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            files.append(f)
    
    # 排除非简历文件（如论文等）
    excluded_keywords = ['论文', 'paper', 'arxiv', '1908.', '1909.', '2020.', '2021.', '2022.', '2023.']
    filtered_files = []
    for f in files:
        if any(kw.lower() in f.lower() for kw in excluded_keywords):
            print(f"⏭️ 跳过非简历文件: {f}")
            continue
        filtered_files.append(f)
    
    print(f"\n📂 源目录: {source_dir}")
    print(f"📄 发现 {len(filtered_files)} 个简历文件")
    print("-" * 50)
    
    # 检查已存在的任务
    existing = set()
    if skip_existing:
        tasks = db.query(ResumeTask).all()
        for t in tasks:
            if t.file_name:
                existing.add(t.file_name)
    
    added = 0
    skipped = 0
    
    for filename in filtered_files:
        # 检查是否已存在
        if filename in existing:
            print(f"⏭️ 已存在: {filename}")
            skipped += 1
            continue
        
        source_path = os.path.join(source_dir, filename)
        ext = os.path.splitext(filename)[1].lower().strip('.')
        
        # 生成唯一文件名并复制到uploads目录
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        dest_path = os.path.join(UPLOAD_DIR, unique_name)
        
        try:
            shutil.copy2(source_path, dest_path)
        except Exception as e:
            print(f"❌ 复制失败: {filename} - {e}")
            continue
        
        # 创建任务
        task = ResumeTask(
            file_path=dest_path,
            file_name=filename,
            file_type=ext,
            status='pending'
        )
        db.add(task)
        added += 1
        print(f"✅ 添加: {filename}")
    
    db.commit()
    db.close()
    
    print("-" * 50)
    print(f"📊 汇总:")
    print(f"   ✅ 新增任务: {added}")
    print(f"   ⏭️ 跳过已存在: {skipped}")
    print(f"   📋 总文件数: {len(filtered_files)}")
    
    if added > 0:
        print(f"\n💡 后台Worker将自动处理这些任务")
        print(f"   查看状态: python resume_worker.py status")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python batch_import_resumes.py <目录路径>")
        print("示例: python batch_import_resumes.py /path/to/resumes")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    batch_import(source_dir)
