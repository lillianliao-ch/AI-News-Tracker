#!/usr/bin/env python3
"""
从字节跳动官网抓取职位详细信息并更新到数据库
"""

import sys
import os
import re
import time
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Job

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def fetch_job_detail(url: str) -> dict:
    """抓取职位详情"""
    try:
        # 规范化URL
        if 'job.toutiao.com' in url:
            # 转换为 jobs.bytedance.com 格式
            match = re.search(r'/detail/(\d+)', url)
            if match:
                job_id = match.group(1)
                url = f"https://jobs.bytedance.com/experienced/position/{job_id}/detail"
        
        print(f"  📥 正在抓取: {url}")
        
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        result = {
            'title': '',
            'location': '',
            'job_code': '',
            'raw_jd_text': '',
        }
        
        # 提取职位名称
        title_el = soup.find('h1') or soup.find('div', class_=re.compile(r'title|name', re.I))
        if title_el:
            result['title'] = title_el.get_text(strip=True)
        
        # 提取职位ID
        job_id_match = re.search(r'职位\s*ID[：:]\s*(\w+)', resp.text)
        if job_id_match:
            result['job_code'] = job_id_match.group(1)
        
        # 提取地点信息
        location_match = re.search(r'(北京|上海|杭州|深圳|广州|成都|武汉|南京|西安)', resp.text)
        if location_match:
            result['location'] = location_match.group(1)
        
        # 提取JD内容 - 查找职位描述和职位要求
        jd_parts = []
        
        # 查找包含"职位描述"或"岗位职责"的部分
        for section_title in ['职位描述', '岗位职责', '工作职责', '职位要求', '岗位要求', '任职要求']:
            section = soup.find(string=re.compile(section_title))
            if section:
                parent = section.find_parent()
                if parent:
                    # 获取后续的内容
                    next_el = parent.find_next_sibling()
                    if next_el:
                        jd_parts.append(f"【{section_title}】")
                        jd_parts.append(next_el.get_text(separator='\n', strip=True))
        
        # 如果上面方法没找到，尝试更通用的方式
        if not jd_parts:
            # 查找所有列表项
            all_text = []
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if len(text) > 10 and len(text) < 500:
                    all_text.append(text)
            
            if all_text:
                jd_parts = all_text
        
        # 组装JD文本
        if jd_parts:
            result['raw_jd_text'] = '\n'.join(jd_parts)
        
        return result
        
    except Exception as e:
        print(f"  ❌ 抓取失败: {e}")
        return None


def main():
    db = SessionLocal()
    
    # 查找所有杜英英团队的职位（raw_jd_text为空或很短的）
    jobs = db.query(Job).filter(
        Job.company == "字节跳动",
        Job.hr_contact == "杜英英",
        Job.jd_link.isnot(None)
    ).all()
    
    print(f"📋 找到 {len(jobs)} 个需要补充JD的职位")
    
    updated = 0
    failed = 0
    
    for job in jobs:
        # 检查是否需要更新
        if job.raw_jd_text and len(job.raw_jd_text) > 100:
            print(f"⏭️  跳过已有JD: {job.title}")
            continue
        
        if not job.jd_link:
            print(f"⏭️  无链接: {job.title}")
            continue
        
        print(f"\n🔍 处理: {job.title}")
        
        detail = fetch_job_detail(job.jd_link)
        
        if detail and detail.get('raw_jd_text'):
            job.raw_jd_text = detail['raw_jd_text']
            
            # 如果抓到了更完整的job_code
            if detail.get('job_code') and not job.job_code:
                job.job_code = detail['job_code']
            
            # 补充地点
            if detail.get('location') and not job.location:
                job.location = detail['location']
            
            db.commit()
            print(f"  ✅ 更新成功 ({len(detail['raw_jd_text'])} 字符)")
            updated += 1
        else:
            print(f"  ⚠️ 未能获取JD内容")
            failed += 1
        
        # 间隔防止被封
        time.sleep(1)
    
    print(f"\n📊 完成: 更新 {updated} 个, 失败 {failed} 个")


if __name__ == "__main__":
    main()
