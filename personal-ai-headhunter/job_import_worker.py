#!/usr/bin/env python3
"""
后台职位导入处理器
用法: 
    python job_import_worker.py          # 前台运行
    nohup python job_import_worker.py &  # 后台运行
"""

import os
import sys
import time
import traceback
import json
import re
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量（必须在其他导入之前）
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from database import SessionLocal, JobImportTask, Job
from sqlalchemy import text

# 配置
POLL_INTERVAL = 5  # 轮询间隔（秒）

# 公司前缀映射文件
MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'company_prefix_map.json')


def load_prefix_map():
    """加载公司前缀映射"""
    try:
        with open(MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def get_correct_prefix(company, title, prefix_map):
    """根据公司和标题确定正确的前缀"""
    if not company:
        company = ""
    if not title:
        title = ""
    
    company_lower = company.lower()
    title_lower = title.lower()
    
    # 从映射表匹配
    for key, val in prefix_map.items():
        if key.lower() in company_lower or company_lower in key.lower():
            return val
    
    # 特殊处理常见公司（从标题推断）
    all_text = company_lower + " " + title_lower
    
    if any(kw in all_text for kw in ['字节', 'bytedance', 'tiktok', '豆包', '飞书', '抖音', 'pico', 'data语音', 'seed', 'flow']):
        return 'BT'
    elif 'minimax' in all_text:
        return 'MMX'
    elif any(kw in all_text for kw in ['阿里', '淘天', '钉钉', '高德', '平头哥', '优酷', '淘宝', '天猫', '菜鸟', '业务技术']):
        return 'ALI'
    elif any(kw in all_text for kw in ['阿里云', 'aliyun']):
        return 'AY'
    elif '小红书' in all_text:
        return 'XHS'
    elif '腾讯' in all_text:
        return 'TX'
    elif '百度' in all_text:
        return 'BD'
    elif '美团' in all_text:
        return 'MT'
    
    return 'OTH'  # 其他


def generate_job_code(db, prefix):
    """生成职位编号"""
    # 查询该前缀下最大序号
    result = db.execute(text(
        f"SELECT job_code FROM jobs WHERE job_code LIKE '{prefix}%' ORDER BY job_code DESC LIMIT 1"
    )).first()
    
    max_num = 0
    if result and result[0]:
        match = re.search(r'(\d+)$', result[0])
        if match:
            max_num = int(match.group(1))
    
    next_num = max_num + 1
    return f"{prefix}{next_num:03d}"


def extract_tags_for_job(job, db):
    """为单个职位提取标签"""
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()
        
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 构建提取请求
        jd_text = job.raw_jd_text or ""
        if not jd_text.strip():
            return False
        
        prompt = f"""请从以下JD中提取结构化标签。

【职位信息】
职位名称: {job.title}
公司: {job.company}
JD内容: {jd_text[:3000]}

请返回JSON格式，包含以下字段：
- tech_domain: 技术方向列表
- core_specialty: 核心专长列表
- tech_skills: 技术技能列表
- role_type: 岗位类型（单选）
- seniority: 职级层次（单选）
- role_orientation: 角色定位列表

只返回JSON，不要其他内容。"""

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        
        # 清理 markdown 代码块
        if result.startswith("```"):
            result = re.sub(r'^```\w*\n?', '', result)
            result = re.sub(r'\n?```$', '', result)
        
        tags = json.loads(result)
        job.structured_tags = json.dumps(tags, ensure_ascii=False)
        db.commit()
        return True
        
    except Exception as e:
        print(f"      ⚠️ 标签提取失败: {e}")
        return False


def process_task(task: JobImportTask, db) -> dict:
    """
    处理单个导入任务
    返回统计结果
    """
    file_path = task.file_path
    file_type = task.file_type or ""
    file_name = task.file_name or ""
    
    print(f"\n{'='*50}")
    print(f"📂 处理任务 #{task.id}: {file_name}")
    print(f"   类型: {file_type}, 路径: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 读取文件
    if file_type.lower() == 'csv':
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    
    print(f"   📊 读取到 {len(df)} 条记录")
    
    # 加载前缀映射
    prefix_map = load_prefix_map()
    
    # 获取现有职位标题（用于去重）
    existing_titles = set()
    existing_jobs = db.query(Job.title).all()
    for j in existing_jobs:
        if j[0]:
            existing_titles.add(j[0].strip().lower())
    
    stats = {
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'tags_extracted': 0,
        'new_job_ids': []
    }
    
    for index, row in df.iterrows():
        try:
            # 智能字段映射
            row_dict = {str(k).strip().lower(): v for k, v in row.items()}
            
            def get_val(keys, default=""):
                for k in keys:
                    for row_k in row_dict:
                        if k in row_k:
                            val = row_dict[row_k]
                            return str(val).strip() if pd.notna(val) else default
                return default
            
            # 提取关键字段
            title = get_val(["职位名称", "职位", "岗位", "title"], "")
            company = get_val(["公司名称", "公司", "company", "部门"], "")
            location = get_val(["工作地点", "地点", "location", "city"])
            salary = get_val(["薪资范围", "薪资", "salary", "pay"])
            experience = get_val(["工作年限", "经验", "experience"])
            department = get_val(["部门", "department"])
            seniority = get_val(["岗位层级", "职级", "seniority"])
            hr = get_val(["hr", "招聘hr", "猎聘hr"])
            jd_link = get_val(["职位链接", "link", "url", "原始链接"])
            
            # 跳过无效行
            if not title or title in ['nan', 'None']:
                continue
            
            # 去重检查
            if title.strip().lower() in existing_titles:
                stats['skipped'] += 1
                continue
            
            # 构建JD文本
            desc = get_val(["岗位描述", "职位描述", "description"])
            req = get_val(["岗位要求", "任职要求", "requirement"])
            
            jd_parts = []
            if desc and desc not in ['nan', 'None']:
                jd_parts.append(f"【岗位描述】:\n{desc}")
            if req and req not in ['nan', 'None']:
                jd_parts.append(f"【岗位要求】:\n{req}")
            
            raw_text = "\n\n".join(jd_parts) if jd_parts else ""
            
            # 提取年限数字
            req_exp = 0
            if experience:
                match = re.search(r'(\d+)', str(experience))
                if match:
                    req_exp = int(match.group(1))
            
            # 生成职位编号
            prefix = get_correct_prefix(company, title, prefix_map)
            job_code = generate_job_code(db, prefix)
            
            # 创建职位
            detail_fields = json.loads(row.to_json())
            
            new_job = Job(
                job_code=job_code,
                title=title,
                company=company,
                department=department,
                location=location,
                salary_range=salary,
                required_experience_years=req_exp,
                seniority_level=seniority,
                hr_contact=hr,
                jd_link=jd_link,
                raw_jd_text=raw_text,
                detail_fields=detail_fields
            )
            
            db.add(new_job)
            db.commit()
            db.refresh(new_job)
            
            stats['imported'] += 1
            stats['new_job_ids'].append(new_job.id)
            existing_titles.add(title.strip().lower())
            
            print(f"   ✅ [{job_code}] {title[:40]}...")
            
        except Exception as e:
            stats['failed'] += 1
            print(f"   ❌ 行 {index}: {e}")
    
    print(f"\n   📊 导入统计: 成功={stats['imported']}, 跳过={stats['skipped']}, 失败={stats['failed']}")
    
    # 为新导入的职位提取标签
    if stats['new_job_ids']:
        print(f"\n   🏷️ 开始提取标签 ({len(stats['new_job_ids'])} 个职位)...")
        for job_id in stats['new_job_ids']:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                success = extract_tags_for_job(job, db)
                if success:
                    stats['tags_extracted'] += 1
                    print(f"      ✅ [{job.job_code}] 标签提取成功")
        
        print(f"   🏷️ 标签提取完成: {stats['tags_extracted']}/{len(stats['new_job_ids'])}")
    
    return stats


def run_worker():
    """运行 worker 主循环"""
    print("="*60)
    print("🚀 职位导入后台处理器已启动")
    print(f"   轮询间隔: {POLL_INTERVAL} 秒")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    while True:
        db = SessionLocal()
        
        try:
            # 查找待处理任务
            task = db.query(JobImportTask).filter(
                JobImportTask.status == 'pending'
            ).order_by(JobImportTask.created_at).first()
            
            if task:
                # 更新状态为处理中
                task.status = 'processing'
                task.started_at = datetime.now()
                db.commit()
                
                try:
                    # 处理任务
                    stats = process_task(task, db)
                    
                    # 更新为完成
                    task.status = 'done'
                    task.jobs_imported = stats['imported']
                    task.jobs_skipped = stats['skipped']
                    task.jobs_failed = stats['failed']
                    task.tags_extracted = stats['tags_extracted']
                    task.finished_at = datetime.now()
                    db.commit()
                    
                    print(f"\n   ✅ 任务 #{task.id} 完成\n")
                    
                except Exception as e:
                    # 更新为失败
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    print(f"   ❌ 任务 #{task.id} 失败: {error_msg}")
                    traceback.print_exc()
                    
                    task.status = 'failed'
                    task.error_message = error_msg
                    task.finished_at = datetime.now()
                    db.commit()
            
        except Exception as e:
            print(f"❌ Worker 错误: {e}")
            traceback.print_exc()
            
        finally:
            db.close()
        
        # 等待下一次轮询
        time.sleep(POLL_INTERVAL)


def show_status():
    """显示任务队列状态"""
    db = SessionLocal()
    
    pending = db.query(JobImportTask).filter(JobImportTask.status == 'pending').count()
    processing = db.query(JobImportTask).filter(JobImportTask.status == 'processing').count()
    done = db.query(JobImportTask).filter(JobImportTask.status == 'done').count()
    failed = db.query(JobImportTask).filter(JobImportTask.status == 'failed').count()
    
    print(f"\n📊 职位导入任务队列状态:")
    print(f"   待处理: {pending}")
    print(f"   处理中: {processing}")
    print(f"   已完成: {done}")
    print(f"   失败:   {failed}")
    
    # 显示最近任务
    recent = db.query(JobImportTask).order_by(JobImportTask.created_at.desc()).limit(5).all()
    if recent:
        print(f"\n📋 最近任务:")
        for t in recent:
            status_icon = {"pending": "⏳", "processing": "🔄", "done": "✅", "failed": "❌"}.get(t.status, "❓")
            result = f"导入{t.jobs_imported}/跳过{t.jobs_skipped}" if t.status == 'done' else t.error_message or ""
            print(f"   {status_icon} #{t.id} {t.file_name} - {t.status} {result}")
    
    db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            show_status()
        elif sys.argv[1] == "once":
            # 只处理一次
            db = SessionLocal()
            task = db.query(JobImportTask).filter(JobImportTask.status == 'pending').first()
            if task:
                task.status = 'processing'
                task.started_at = datetime.now()
                db.commit()
                try:
                    stats = process_task(task, db)
                    task.status = 'done'
                    task.jobs_imported = stats['imported']
                    task.jobs_skipped = stats['skipped']
                    task.jobs_failed = stats['failed']
                    task.tags_extracted = stats['tags_extracted']
                except Exception as e:
                    task.status = 'failed'
                    task.error_message = str(e)
                task.finished_at = datetime.now()
                db.commit()
            else:
                print("无待处理任务")
            db.close()
        else:
            print("用法:")
            print("  python job_import_worker.py          # 启动 worker")
            print("  python job_import_worker.py status   # 查看队列状态")
            print("  python job_import_worker.py once     # 只处理一个任务")
    else:
        run_worker()
