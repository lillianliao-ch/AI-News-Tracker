#!/usr/bin/env python3
"""
测试后台 API
"""

import base64
import json
import requests
from pathlib import Path


def test_process_candidate():
    """测试候选人处理接口"""
    
    # 1. 读取测试简历
    resume_path = Path("/Users/lillianliao/Downloads/【专有云安全专家_北京_70-100K】陈川_13年.pdf")
    
    if not resume_path.exists():
        print(f"❌ 简历文件不存在: {resume_path}")
        return
    
    print(f"📄 读取简历: {resume_path.name}")
    
    # 2. 转换为 Base64
    with open(resume_path, 'rb') as f:
        pdf_bytes = f.read()
        resume_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    print(f"✅ 简历已编码 (Base64 长度: {len(resume_base64)})")
    
    # 3. 构造请求数据
    request_data = {
        "candidate_info": {
            "name": "陈川",
            "source_platform": "Boss直聘",
            "current_company": "天翼云科技有限公司",
            "current_position": "研发专家",
            "work_years": 13,
            "expected_salary": "70-100K",
            "education": "硕士",
            "active_status": "本周活跃"
        },
        "resume_file": resume_base64,
        "jd_config": {
            "position": "AI产品经理（C端）",
            "location": ["北京", "深圳"],
            "salary_range": "30-60K",
            "work_years": "3-5年",
            "education": "本科及以上",
            "required_skills": [
                "AI产品经验（2年以上）",
                "C端产品（DAU>100万）",
                "大模型应用（RAG/Agent）"
            ],
            "optional_skills": [
                "大厂背景（BAT/字节/美团等）",
                "0-1产品经验",
                "B端+C端复合背景"
            ]
        }
    }
    
    # 4. 发送请求
    print("\n🚀 发送请求到后台 API...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/candidates/process",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "="*80)
            print("✅ API 测试成功！")
            print("="*80)
            
            print(f"\n📋 候选人ID: {result['candidate_id']}")
            print(f"⏱️  处理时间: {result['processing_time']} 秒")
            
            # 基本信息
            basic_info = result['structured_resume']['基本信息']
            print(f"\n【基本信息】")
            print(f"  姓名: {basic_info.get('姓名', 'N/A')}")
            print(f"  公司: {basic_info.get('当前公司', 'N/A')}")
            print(f"  职位: {basic_info.get('当前职位', 'N/A')}")
            print(f"  年限: {basic_info.get('工作年限', 'N/A')} 年")
            
            # 评估结果
            evaluation = result['evaluation']
            print(f"\n【评估结果】")
            print(f"  综合匹配度: {evaluation['综合匹配度']}%")
            print(f"  推荐等级: {evaluation['推荐等级']}")
            print(f"  核心优势: {', '.join(evaluation['核心优势'][:3])}")
            
            # 保存完整结果
            output_file = "api_test_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 完整结果已保存: {output_file}")
            
        else:
            print(f"\n❌ API 请求失败")
            print(f"响应内容: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ 请求超时（60秒）")
    
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")


if __name__ == "__main__":
    print("🧪 开始测试后台 API\n")
    test_process_candidate()
    print("\n✅ 测试完成！")

