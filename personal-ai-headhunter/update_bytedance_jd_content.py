#!/usr/bin/env python3
"""
更新字节跳动职位的JD内容 - 从官网链接获取完整职位描述
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, Job
import requests
from bs4 import BeautifulSoup
import time
import re

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def fetch_jd_content(url):
    """从字节跳动招聘页面获取JD内容"""
    try:
        # 转换URL格式
        if 'job.toutiao.com' in url:
            # 旧格式转新格式
            match = re.search(r'/detail/(\d+)', url)
            if match:
                job_id = match.group(1)
                url = f"https://jobs.bytedance.com/experienced/position/{job_id}/detail"
        
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 尝试多种方式提取内容
        content_parts = []
        
        # 方法1: 查找职位描述区域
        for selector in ['.job-detail', '.position-detail', '.job-content', 'article', '.content']:
            elements = soup.select(selector)
            for el in elements:
                text = el.get_text(separator='\n', strip=True)
                if len(text) > 100:
                    content_parts.append(text)
        
        # 方法2: 查找包含关键词的段落
        if not content_parts:
            for p in soup.find_all(['p', 'div', 'li']):
                text = p.get_text(strip=True)
                if any(kw in text for kw in ['职位描述', '职位要求', '工作职责', '任职要求']):
                    parent = p.parent
                    if parent:
                        content_parts.append(parent.get_text(separator='\n', strip=True))
        
        if content_parts:
            # 去重并合并
            seen = set()
            result = []
            for part in content_parts:
                if part not in seen:
                    seen.add(part)
                    result.append(part)
            return '\n\n'.join(result)[:5000]  # 限制长度
        
        return None
        
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return None


def main():
    db = next(get_db())
    
    # 获取所有字节跳动职位
    jobs = db.query(Job).filter(
        Job.company == "字节跳动",
        Job.jd_link.isnot(None)
    ).all()
    
    print(f"📋 找到 {len(jobs)} 个字节跳动职位需要更新JD内容\n")
    
    updated = 0
    failed = 0
    
    for i, job in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] {job.job_code} | {job.title}")
        
        # 检查是否已有详细内容
        if job.raw_jd_text and len(job.raw_jd_text) > 200 and '请访问原始JD链接' not in job.raw_jd_text:
            print(f"  ⏭️ 已有详细内容，跳过")
            continue
        
        if not job.jd_link:
            print(f"  ⏭️ 无JD链接，跳过")
            continue
        
        # 获取JD内容
        print(f"  🔗 获取: {job.jd_link}")
        content = fetch_jd_content(job.jd_link)
        
        if content and len(content) > 100:
            job.raw_jd_text = content
            db.commit()
            print(f"  ✅ 更新成功 ({len(content)} 字符)")
            updated += 1
        else:
            print(f"  ❌ 获取失败或内容太短")
            failed += 1
        
        # 避免请求过快
        time.sleep(1)
    
    print(f"\n📊 更新完成: 成功 {updated} 个, 失败 {failed} 个")


if __name__ == "__main__":
    main()
