#!/usr/bin/env python3
"""
后台简历解析处理器
用法: 
    python resume_worker.py          # 前台运行
    nohup python resume_worker.py &  # 后台运行
"""

import os
import sys
import time
import traceback
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, ResumeTask, Candidate
from ai_service import AIService

# 配置
POLL_INTERVAL = 5  # 轮询间隔（秒）
MAX_RETRIES = 3    # 最大重试次数


def estimate_age_from_education(education_details: list) -> int:
    """
    根据教育经历推算年龄
    逻辑：找到最早的入学年份，根据学历类型推算出生年份
    - 本科入学通常18岁
    - 硕士入学通常22岁  
    - 博士入学通常24岁
    - 大专入学通常18岁
    """
    import re
    from datetime import datetime
    
    if not education_details or not isinstance(education_details, list):
        return None
    
    earliest_year = None
    earliest_degree = None
    
    for edu in education_details:
        if not isinstance(edu, dict):
            continue
            
        # 尝试从 year/time/time_range 等字段提取年份
        time_str = edu.get('year') or edu.get('time') or edu.get('time_range') or ''
        degree_raw = edu.get('degree', '')
        degree = str(degree_raw).lower() if degree_raw else ''
        
        # 提取年份（找第一个4位数年份作为入学年份）
        years = re.findall(r'(19\d{2}|20\d{2})', str(time_str))
        if years:
            start_year = int(years[0])  # 第一个年份作为入学年份
            
            if earliest_year is None or start_year < earliest_year:
                earliest_year = start_year
                earliest_degree = degree
    
    if not earliest_year:
        return None
    
    # 根据学历推算入学年龄
    if '博士' in (earliest_degree or ''):
        entry_age = 24
    elif '硕士' in (earliest_degree or ''):
        entry_age = 22
    elif '本科' in (earliest_degree or '') or '学士' in (earliest_degree or ''):
        entry_age = 18
    elif '大专' in (earliest_degree or '') or '专科' in (earliest_degree or ''):
        entry_age = 18
    else:
        entry_age = 18  # 默认按本科算
    
    # 推算出生年份
    birth_year = earliest_year - entry_age
    
    # 计算当前年龄
    current_year = datetime.now().year
    age = current_year - birth_year
    
    # 合理性检验
    if 18 <= age <= 70:
        return age
    
    return None


def process_task(task: ResumeTask, db) -> bool:
    """
    处理单个任务
    返回 True 表示成功，False 表示失败
    """
    file_path = task.file_path
    file_type = task.file_type or ""
    file_name = task.file_name or ""
    
    print(f"\n{'='*50}")
    print(f"📄 处理任务 #{task.id}: {file_name}")
    print(f"   类型: {file_type}, 路径: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 根据文件类型处理
    text = ""
    parsed = None
    
    if file_type.lower() in ['pdf', 'txt']:
        # 文本类简历
        if file_type.lower() == 'pdf':
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        # 如果PDF提取不到文字，尝试OCR
        if not text.strip() and file_type.lower() == 'pdf':
            print(f"   ⚠️ PDF无法提取文字，尝试OCR...")
            try:
                import fitz  # PyMuPDF
                import base64
                from io import BytesIO
                from PIL import Image
                
                doc = fitz.open(file_path)
                images_data = []
                
                for page_num in range(min(len(doc), 5)):  # 最多处理5页
                    page = doc[page_num]
                    # 渲染为图片
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放提高质量
                    img_data = pix.tobytes("png")
                    images_data.append(base64.b64encode(img_data).decode('utf-8'))
                
                doc.close()
                
                if images_data:
                    # 对第一张图片进行OCR
                    print(f"   🖼️ 转换为图片，共 {len(images_data)} 页，开始OCR...")
                    parsed = AIService.ocr_resume_image(images_data[0])
                    text = parsed.get("raw_text", "")
                    
            except ImportError:
                print(f"   ❌ 需要安装 PyMuPDF: pip install PyMuPDF")
                raise ValueError("扫描版PDF需要PyMuPDF库进行OCR")
            except Exception as ocr_error:
                print(f"   ❌ OCR失败: {ocr_error}")
                raise ValueError(f"OCR处理失败: {ocr_error}")
        
        if not text.strip():
            raise ValueError("文件内容为空")
        
        print(f"   📝 提取文本 {len(text)} 字符")
        
        # 如果还没解析过（非OCR路径），调用 AI 解析
        if not parsed:
            parsed = AIService.parse_resume(text)
        
    elif file_type.lower() in ['jpg', 'jpeg', 'png', 'webp']:
        # 图片类简历 - OCR
        import base64
        with open(file_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        print(f"   🖼️ 图片OCR识别中...")
        
        # 调用 OCR
        parsed = AIService.ocr_resume_image(image_data)
        text = parsed.get("raw_text", "")
        
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")
    
    # 检查解析结果
    if not parsed or parsed.get("name") == "Parse Error":
        error_msg = parsed.get("summary", "解析失败") if parsed else "解析返回空"
        raise ValueError(error_msg)
    
    name = parsed.get("name", "未知")
    print(f"   ✅ 解析成功: {name}")
    
    # 获取年龄，如果AI解析没有返回，则根据教育经历推算
    age = parsed.get("age")
    education_details = parsed.get("education_details", [])
    
    if not age and education_details:
        age = estimate_age_from_education(education_details)
        if age:
            print(f"   📅 根据教育经历推算年龄: {age}岁")
    
    # 创建候选人
    candidate = Candidate(
        name=name,
        email=parsed.get("email"),
        phone=parsed.get("phone"),
        age=age,
        raw_resume_text=text if file_type.lower() in ['pdf', 'txt'] else parsed.get("raw_text", ""),
        source_file=file_name,
        ai_summary=parsed.get("summary"),
        skills=parsed.get("skills", []),
        experience_years=parsed.get("experience_years"),
        education_level=parsed.get("education_level"),
        education_details=education_details,
        work_experiences=parsed.get("work_experiences", []),
        project_experiences=parsed.get("project_experiences", []),
        current_company=parsed.get("current_company"),
        current_title=parsed.get("current_title"),
        expect_location=parsed.get("expect_location"),
        source=f"后台解析-{file_type.upper()}"
    )
    
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    print(f"   💾 已创建候选人 ID: {candidate.id}")
    
    return candidate.id


def run_worker():
    """运行 worker 主循环"""
    print("="*60)
    print("🚀 简历解析后台处理器已启动")
    print(f"   轮询间隔: {POLL_INTERVAL} 秒")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    while True:
        db = SessionLocal()
        
        try:
            # 查找待处理任务
            task = db.query(ResumeTask).filter(
                ResumeTask.status == 'pending'
            ).order_by(ResumeTask.created_at).first()
            
            if task:
                # 更新状态为处理中
                task.status = 'processing'
                task.started_at = datetime.now()
                db.commit()
                
                try:
                    # 处理任务
                    candidate_id = process_task(task, db)
                    
                    # 更新为完成
                    task.status = 'done'
                    task.candidate_id = candidate_id
                    task.finished_at = datetime.now()
                    db.commit()
                    
                    print(f"   ✅ 任务 #{task.id} 完成")
                    
                except Exception as e:
                    # 更新为失败
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    print(f"   ❌ 任务 #{task.id} 失败: {error_msg}")
                    traceback.print_exc()
                    
                    task.status = 'failed'
                    task.error_message = error_msg
                    task.finished_at = datetime.now()
                    db.commit()
            
            else:
                # 无待处理任务，等待
                pass
                
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
    
    pending = db.query(ResumeTask).filter(ResumeTask.status == 'pending').count()
    processing = db.query(ResumeTask).filter(ResumeTask.status == 'processing').count()
    done = db.query(ResumeTask).filter(ResumeTask.status == 'done').count()
    failed = db.query(ResumeTask).filter(ResumeTask.status == 'failed').count()
    
    print(f"\n📊 任务队列状态:")
    print(f"   待处理: {pending}")
    print(f"   处理中: {processing}")
    print(f"   已完成: {done}")
    print(f"   失败:   {failed}")
    
    # 显示最近任务
    recent = db.query(ResumeTask).order_by(ResumeTask.created_at.desc()).limit(5).all()
    if recent:
        print(f"\n📋 最近任务:")
        for t in recent:
            status_icon = {"pending": "⏳", "processing": "🔄", "done": "✅", "failed": "❌"}.get(t.status, "❓")
            print(f"   {status_icon} #{t.id} {t.file_name} - {t.status}")
    
    db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            show_status()
        elif sys.argv[1] == "once":
            # 只处理一次
            db = SessionLocal()
            task = db.query(ResumeTask).filter(ResumeTask.status == 'pending').first()
            if task:
                task.status = 'processing'
                task.started_at = datetime.now()
                db.commit()
                try:
                    cid = process_task(task, db)
                    task.status = 'done'
                    task.candidate_id = cid
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
            print("  python resume_worker.py          # 启动 worker")
            print("  python resume_worker.py status   # 查看队列状态")
            print("  python resume_worker.py once     # 只处理一个任务")
    else:
        run_worker()
