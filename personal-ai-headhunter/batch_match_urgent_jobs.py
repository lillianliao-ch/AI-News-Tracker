#!/usr/bin/env python3
"""
紧急职位批量匹配 - 逐步验证版本
每个关键步骤都有验证点，确保数据质量
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from job_search import search_candidates
import json
from datetime import datetime

# 配置
DB_PATH = 'data/headhunter.db'
MIN_URGENCY = 1
TOP_K = 10
MIN_SCORE = 0.3

def build_search_query(job):
    """从职位信息构建搜索查询"""
    parts = []

    if job.title:
        parts.append(job.title)
    if job.company:
        parts.append(job.company)

    # 添加经验要求
    if job.required_experience_years:
        parts.append(f"{job.required_experience_years}年以上经验")

    # 添加地点
    if job.location:
        parts.append(job.location)

    return " ".join(parts)

def wait_for_verification(prompt="\n按 Enter 继续，或输入 'q' 退出: "):
    """等待用户确认"""
    user_input = input(prompt)
    if user_input.lower() == 'q':
        print("⚠️  用户取消执行")
        return False
    return True

# ============================================================================
# 验证点 1: 数据库连接
# ============================================================================
def verify_database():
    """验证数据库连接和基础数据"""
    print("\n" + "="*80)
    print("🔍 验证点 1/5: 数据库连接")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        print(f"💡 请先运行应用初始化数据库")
        return False
    
    try:
        engine = create_engine(f'sqlite:///{DB_PATH}')
        
        with engine.connect() as conn:
            # 检查表是否存在
            tables = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('jobs', 'candidates')
            """)).fetchall()
            
            if len(tables) < 2:
                print("❌ 数据表不存在")
                print(f"💡 找到的表: {[t[0] for t in tables]}")
                return False
            
            # 获取基础统计
            job_count = conn.execute(text("SELECT COUNT(*) FROM jobs")).fetchone()[0]
            candidate_count = conn.execute(text("SELECT COUNT(*) FROM candidates")).fetchone()[0]
            
            print(f"✅ 数据库文件存在: {DB_PATH}")
            print(f"✅ jobs 表: {job_count} 条记录")
            print(f"✅ candidates 表: {candidate_count} 条记录")
            print()
            print("📊 数据快照:")
            print(f"  - 职位总数: {job_count}")
            print(f"  - 候选人总数: {candidate_count}")
            
            # 显示示例数据
            if job_count > 0:
                sample_job = conn.execute(text("""
                    SELECT id, title, company, urgency FROM jobs 
                    ORDER BY urgency DESC, id DESC 
                    LIMIT 3
                """)).fetchall()
                
                print(f"\n  职位示例:")
                for j in sample_job:
                    urgency_mark = "🔴" if j.urgency == 3 else "🟡" if j.urgency == 2 else "🟢" if j.urgency == 1 else ""
                    print(f"    ID {j.id}: {urgency_mark} {j.title} - {j.company}")
            
            if candidate_count > 0:
                sample_cand = conn.execute(text("""
                    SELECT id, name, current_title, current_company FROM candidates
                    WHERE current_title IS NOT NULL
                    ORDER BY id DESC
                    LIMIT 3
                """)).fetchall()

                print(f"\n  候选人示例:")
                for c in sample_cand:
                    print(f"    ID {c.id}: {c.name} - {c.current_title} @ {c.current_company}")
        
        print("\n✅ 数据库连接验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

# ============================================================================
# 验证点 2: 数据完整性
# ============================================================================
def verify_data_integrity():
    """验证数据完整性和质量"""
    print("\n" + "="*80)
    print("🔍 验证点 2/5: 数据完整性")
    print("="*80)
    
    engine = create_engine(f'sqlite:///{DB_PATH}')
    
    with engine.connect() as conn:
        # 紧急职位检查
        urgent_jobs = conn.execute(text("""
            SELECT COUNT(*) FROM jobs WHERE urgency > 0
        """)).fetchone()[0]
        
        total_jobs = conn.execute(text("SELECT COUNT(*) FROM jobs")).fetchone()[0]
        
        print(f"✅ 职位数据: {total_jobs} 个职位, {urgent_jobs} 个紧急")
        
        if urgent_jobs == 0:
            print("⚠️  没有紧急职位，将使用所有职位")
        
        # 候选人向量检查
        from job_search import CANDIDATE_VECTOR_CACHE_PATH
        vector_index_exists = os.path.exists(CANDIDATE_VECTOR_CACHE_PATH)

        if vector_index_exists:
            import pickle
            with open(CANDIDATE_VECTOR_CACHE_PATH, 'rb') as f:
                vector_index = pickle.load(f)
            candidates_with_vector = len(vector_index)
        else:
            candidates_with_vector = 0

        total_candidates = conn.execute(text("SELECT COUNT(*) FROM candidates")).fetchone()[0]

        print(f"✅ 候选人数据: {total_candidates} 个, {candidates_with_vector} 个有向量索引")
        if vector_index_exists:
            print(f"  📦 向量索引: {CANDIDATE_VECTOR_CACHE_PATH}")
        
        # 联系方式检查
        with_phone = conn.execute(text("""
            SELECT COUNT(*) FROM candidates WHERE phone IS NOT NULL
        """)).fetchone()[0]
        
        with_wechat = conn.execute(text("""
            SELECT COUNT(*) FROM candidates WHERE wechat_id IS NOT NULL
        """)).fetchone()[0]
        
        with_linkedin = conn.execute(text("""
            SELECT COUNT(*) FROM candidates WHERE linkedin_url IS NOT NULL
        """)).fetchone()[0]
        
        with_any_contact = conn.execute(text("""
            SELECT COUNT(*) FROM candidates 
            WHERE phone IS NOT NULL OR wechat_id IS NOT NULL OR linkedin_url IS NOT NULL
        """)).fetchone()[0]
        
        contact_rate = (with_any_contact / total_candidates * 100) if total_candidates > 0 else 0
        
        print(f"\n📱 联系方式完整度: {contact_rate:.1f}% ({with_any_contact}/{total_candidates})")
        print(f"  - 手机: {with_phone}")
        print(f"  - 微信: {with_wechat}")
        print(f"  - LinkedIn: {with_linkedin}")
        
        if contact_rate < 50:
            print(f"⚠️  警告: 联系方式完整度低于 50%")
            print(f"💡 建议: 只显示有联系方式的候选人")

        # 来源分布（替代人才等级分布）
        source_stats = conn.execute(text("""
            SELECT
                COALESCE(source, 'Unknown') as source,
                COUNT(*) as count
            FROM candidates
            GROUP BY source
            ORDER BY count DESC
        """)).fetchall()

        print(f"\n📊 候选人来源分布:")
        for row in source_stats:
            source = row.source
            count = row.count
            print(f"  {source}: {count} 人")
        
        # 问题汇总
        issues = []
        warnings = []

        if urgent_jobs == 0:
            issues.append("没有紧急职位")
        if not vector_index_exists or candidates_with_vector == 0:
            issues.append("没有可向量匹配的候选人")
        if contact_rate < 30:
            warnings.append("联系方式严重缺失（仅显示有联系方式的候选人）")

        if issues:
            print(f"\n⚠️  发现问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

            print(f"\n💡 建议:")
            if "没有紧急职位" in issues:
                print("  - 为现有职位添加紧急度标记")
                print("  - SQL: UPDATE jobs SET urgency = 2 WHERE ...")
            if "没有可向量匹配的候选人" in issues:
                print("  - 运行: python build_candidate_vectors.py")

            return False

        if warnings:
            print(f"\n⚠️  警告:")
            for warning in warnings:
                print(f"  - {warning}")
            print(f"\n💡 将继续执行，但会优先显示有联系方式的候选人")

        print("\n✅ 数据完整性验证通过")
        return True

# ============================================================================
# 验证点 3: 向量索引
# ============================================================================
def verify_vector_index():
    """验证向量索引和API"""
    print("\n" + "="*80)
    print("🔍 验证点 3/5: 向量索引")
    print("="*80)
    
    from job_search import VECTOR_CACHE_PATH, CANDIDATE_VECTOR_CACHE_PATH, get_embedding
    
    # 检查索引文件
    job_index_exists = os.path.exists(VECTOR_CACHE_PATH)
    candidate_index_exists = os.path.exists(CANDIDATE_VECTOR_CACHE_PATH)
    
    print(f"职位向量索引: {'✅' if job_index_exists else '❌'} {VECTOR_CACHE_PATH}")
    print(f"候选人向量索引: {'✅' if candidate_index_exists else '❌'} {CANDIDATE_VECTOR_CACHE_PATH}")
    
    if not job_index_exists:
        print(f"\n💡 需要构建职位索引:")
        print(f"  python build_job_index.py")
        return False
    
    # 测试 Embedding API
    print(f"\n🧪 测试 Embedding API...")
    try:
        test_embedding = get_embedding("测试文本")
        if test_embedding and len(test_embedding) > 0:
            print(f"✅ Embedding API 可用 (向量维度: {len(test_embedding)})")
        else:
            print(f"❌ Embedding API 返回空向量")
            return False
    except Exception as e:
        print(f"❌ Embedding API 调用失败: {e}")
        print(f"💡 请检查 DASHSCOPE_API_KEY 或 OPENAI_API_KEY")
        return False
    
    print("\n✅ 向量索引验证通过")
    return True

# ============================================================================
# 验证点 4: 单职位测试匹配
# ============================================================================
def verify_single_match():
    """对单个紧急职位进行测试匹配"""
    print("\n" + "="*80)
    print("🔍 验证点 4/5: 单职位测试匹配")
    print("="*80)
    
    engine = create_engine(f'sqlite:///{DB_PATH}')
    
    # 获取一个紧急职位
    with engine.connect() as conn:
        job = conn.execute(text("""
            SELECT id, title, company, urgency, salary_range,
                   location, required_experience_years
            FROM jobs
            WHERE urgency > 0
            ORDER BY urgency DESC, id DESC
            LIMIT 1
        """)).fetchone()
    
    if not job:
        print("❌ 没有找到紧急职位")
        return False
    
    print(f"📋 测试职位:")
    print(f"  标题: {job.title}")
    print(f"  公司: {job.company}")
    print(f"  紧急度: {job.urgency}")
    print(f"  薪资: {job.salary_range}")
    if job.required_experience_years:
        print(f"  经验要求: {job.required_experience_years}年以上")
    
    # 执行匹配
    print(f"\n🔍 执行匹配...")

    # 构建搜索查询
    search_query = build_search_query(job)
    print(f"📝 搜索查询: {search_query}")

    try:
        matches = search_candidates(
            query=search_query,
            top_k=TOP_K,
            min_score=MIN_SCORE
        )
        
        if not matches:
            print(f"❌ 未找到匹配候选人")
            print(f"💡 建议:")
            print(f"  - 降低 MIN_SCORE (当前: {MIN_SCORE})")
            print(f"  - 增加 TOP_K (当前: {TOP_K})")
            return False
        
        # 分析匹配结果
        scores = [m.get('score', 0) / 100 for m in matches]  # 转换为0-1范围
        high_quality = sum(1 for s in scores if s >= 0.7)
        medium_quality = sum(1 for s in scores if 0.5 <= s < 0.7)
        low_quality = sum(1 for s in scores if s < 0.5)

        print(f"\n🎯 匹配结果 ({len(matches)} 个候选人):")
        print(f"  🔥 高质量(>0.7): {high_quality}")
        print(f"  ✅ 中等匹配(0.5-0.7): {medium_quality}")
        print(f"  📌 低质量(<0.5): {low_quality}")
        print(f"  📈 最高分: {max(scores):.3f}" if scores else "  📈 最高分: N/A")
        print(f"  📊 平均分: {sum(scores)/len(scores):.3f}" if scores else "  📊 平均分: N/A")

        # 显示 Top 3
        print(f"\n📊 Top 3 候选人预览:")
        for i, match in enumerate(matches[:3], 1):
            name = match.get('name', '未知')
            title = match.get('title', '')
            company = match.get('company', '')
            score = match.get('score', 0) / 100  # 转换为0-1范围
            match_reasons = match.get('match_reasons', [])

            print(f"  {i}. {name} - {score:.1%}")
            print(f"     {title} @ {company}")
            if match_reasons:
                print(f"     匹配理由: {', '.join(match_reasons)}")
        
        # 计算质量分
        quality_score = 0
        if high_quality > 0:
            quality_score += 40
        if medium_quality > 0:
            quality_score += 30
        if high_quality + medium_quality >= 3:
            quality_score += 30  # 有足够的候选
        
        print(f"\n📊 质量评分: {quality_score}/100")
        
        if quality_score >= 70:
            print(f"  ✅ 优秀 - 可以继续")
        elif quality_score >= 50:
            print(f"  🟡 良好 - 建议调整参数")
        else:
            print(f"  🔴 需改进 - 建议降低阈值")
        
        return quality_score >= 50
        
    except Exception as e:
        print(f"❌ 匹配失败: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# 验证点 5: 全量匹配
# ============================================================================
def verify_full_match():
    """执行全量匹配并验证"""
    print("\n" + "="*80)
    print("🔍 验证点 5/5: 全量匹配")
    print("="*80)
    
    engine = create_engine(f'sqlite:///{DB_PATH}')
    
    # 获取所有紧急职位
    with engine.connect() as conn:
        jobs = conn.execute(text("""
            SELECT id, title, company, urgency,
                   salary_range, location, required_experience_years,
                   notes
            FROM jobs
            WHERE urgency >= :min_urgency
            ORDER BY urgency DESC, created_at DESC
        """), {"min_urgency": MIN_URGENCY}).fetchall()
    
    if not jobs:
        print("❌ 没有找到紧急职位")
        return False
    
    print(f"✅ 找到 {len(jobs)} 个职位\n")
    
    # 批量匹配
    matched_jobs = []
    total_matches = 0
    quality_scores = []
    
    for idx, job in enumerate(jobs, 1):
        urgency_map = {1: "🟢 较急", 2: "🟡 紧急", 3: "🔴 非常紧急"}
        urgency_text = urgency_map.get(job.urgency, f"未知({job.urgency})")
        
        print(f"\n[{idx}/{len(jobs)}] {urgency_text} {job.title} - {job.company}")

        try:
            # 构建搜索查询
            search_query = build_search_query(job)

            matches = search_candidates(
                query=search_query,
                top_k=TOP_K,
                min_score=MIN_SCORE
            )

            # 计算质量分
            scores = [m.get('score', 0) / 100 for m in matches]  # 转换为0-1范围
            quality_ok = len(matches) > 0 and max(scores) >= 0.5

            matched_jobs.append({
                'job': job,
                'matches': matches,
                'count': len(matches),
                'quality_ok': quality_ok
            })

            total_matches += len(matches)

            # 简要输出
            if matches:
                max_score = max(scores)
                high_q = sum(1 for s in scores if s >= 0.7)
                print(f"  ✅ 找到 {len(matches)} 个候选人 (最高分: {max_score:.2f}, 高质量: {high_q}个)")
            else:
                print(f"  ⚠️  未找到匹配")
                quality_ok = False

            quality_scores.append(1 if quality_ok else 0)
            
        except Exception as e:
            print(f"  ❌ 匹配失败: {e}")
            quality_scores.append(0)
    
    # 汇总
    print(f"\n{'='*80}")
    print(f"📊 匹配完成")
    print(f"{'='*80}")
    print(f"✅ 已匹配职位: {len(matched_jobs)}/{len(jobs)}")
    print(f"✅ 总候选人数: {total_matches}")
    print(f"📈 平均每职位: {total_matches/len(jobs):.1f} 个候选人")
    
    success_rate = sum(quality_scores) / len(quality_scores) * 100
    print(f"✅ 成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print(f"  🌟 优秀 - 可以生成报告")
    elif success_rate >= 50:
        print(f"  ✅ 良好 - 可以生成报告")
    else:
        print(f"  ⚠️  建议检查匹配参数")
    
    return success_rate >= 50, matched_jobs

# ============================================================================
# 生成匹配报告
# ============================================================================
def generate_matching_report(matched_jobs):
    """生成详细的匹配清单报告"""
    from datetime import datetime
    import os

    # 创建 reports 目录
    os.makedirs('reports', exist_ok=True)

    # 生成报告文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f'reports/urgent_jobs_matching_{timestamp}.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        # 标题
        f.write("# 紧急职位智能匹配清单\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**匹配配置**: MIN_URGENCY={MIN_URGENCY}, TOP_K={TOP_K}, MIN_SCORE={MIN_SCORE}\n\n")

        # 摘要
        f.write("## 📊 匹配摘要\n\n")
        total_jobs = len(matched_jobs)
        total_candidates = sum(m['count'] for m in matched_jobs)
        avg_candidates = total_candidates / total_jobs if total_jobs > 0 else 0

        high_quality_jobs = sum(1 for m in matched_jobs if m['quality_ok'])

        f.write(f"- **职位数量**: {total_jobs} 个\n")
        f.write(f"- **候选人数**: {total_candidates} 人\n")
        f.write(f"- **平均每职位**: {avg_candidates:.1f} 人\n")
        f.write(f"- **高质量匹配**: {high_quality_jobs}/{total_jobs} 个职位\n\n")

        # 统计候选人质量分布
        all_scores = []
        for m in matched_jobs:
            scores = [match.get('score', 0) / 100 for match in m['matches']]
            all_scores.extend(scores)

        if all_scores:
            high_q = sum(1 for s in all_scores if s >= 0.7)
            medium_q = sum(1 for s in all_scores if 0.5 <= s < 0.7)
            low_q = sum(1 for s in all_scores if s < 0.5)

            f.write("### 候选人质量分布\n\n")
            f.write(f"| 质量等级 | 数量 | 占比 |\n")
            f.write(f"|---------|------|------|\n")
            f.write(f"| 🔥 高质量 (≥70%) | {high_q} | {high_q/len(all_scores)*100:.1f}% |\n")
            f.write(f"| ✅ 中等匹配 (50-70%) | {medium_q} | {medium_q/len(all_scores)*100:.1f}% |\n")
            f.write(f"| 📌 低质量 (<50%) | {low_q} | {low_q/len(all_scores)*100:.1f}% |\n\n")

        f.write("---\n\n")

        # 职位详情
        for idx, matched_job in enumerate(matched_jobs, 1):
            job = matched_job['job']
            matches = matched_job['matches']
            urgency_map = {1: "较急", 2: "紧急", 3: "非常紧急"}
            urgency_text = urgency_map.get(job.urgency, str(job.urgency))
            urgency_emoji = {1: "🟢", 2: "🟡", 3: "🔴"}.get(job.urgency, "")

            f.write(f"## {idx}. {urgency_emoji} {urgency_text} - {job.title}\n\n")
            f.write(f"**公司**: {job.company}\n\n")

            if job.salary_range:
                f.write(f"**薪资**: {job.salary_range}\n\n")
            if job.location:
                f.write(f"**地点**: {job.location}\n\n")
            if job.required_experience_years:
                f.write(f"**经验要求**: {job.required_experience_years}年以上\n\n")

            # 候选人列表
            f.write(f"### 推荐候选人 ({len(matches)} 人)\n\n")

            if not matches:
                f.write("*未找到匹配候选人*\n\n")
                continue

            for i, match in enumerate(matches, 1):
                name = match.get('name', '未知')
                title = match.get('title', '')
                company = match.get('company', '')
                score = match.get('score', 0) / 100
                match_reasons = match.get('match_reasons', [])

                # 获取候选人详细信息
                try:
                    engine = create_engine(f'sqlite:///{DB_PATH}')
                    with engine.connect() as conn:
                        cand = conn.execute(text("""
                            SELECT phone, wechat_id, linkedin_url, is_friend
                            FROM candidates
                            WHERE id = :cid
                        """), {"cid": match.get('id')}).fetchone()

                        phone = cand.phone if cand else None
                        wechat = cand.wechat_id if cand else None
                        linkedin = cand.linkedin_url if cand else None
                        is_friend = cand.is_friend if cand else 0
                except:
                    phone = wechat = linkedin = is_friend = None

                # 质量等级
                if score >= 0.7:
                    quality = "🔥 高度匹配"
                elif score >= 0.5:
                    quality = "✅ 匹配良好"
                else:
                    quality = "📌 基本匹配"

                # 联系方式
                contact_info = []
                if is_friend:
                    contact_info.append("✅ 已加好友")
                if phone:
                    contact_info.append(f"📱 {phone}")
                if wechat:
                    contact_info.append(f"💬 {wechat}")
                if linkedin:
                    contact_info.append(f"🔗 LinkedIn")

                contact_str = " | ".join(contact_info) if contact_info else "⚠️ 无联系方式"

                f.write(f"#### {i}. {name} - {score:.1%} {quality}\n\n")
                f.write(f"- **职位**: {title} @ {company}\n")
                f.write(f"- **联系方式**: {contact_str}\n")

                if match_reasons:
                    f.write(f"- **匹配理由**: {', '.join(match_reasons)}\n")

                f.write("\n")

            f.write("---\n\n")

        # 跟踪表格模板
        f.write("## 📝 沟通跟进表\n\n")
        f.write("使用此表格记录沟通进度：\n\n")
        f.write("| 职位 | 候选人 | 联系方式 | 沟通日期 | 状态 | 备注 |\n")
        f.write("|------|--------|---------|---------|------|------|\n")

        for matched_job in matched_jobs:
            job = matched_job['job']
            for match in matched_job['matches'][:3]:  # 只列出前3个
                name = match.get('name', '未知')
                f.write(f"| {job.title} | {name} |  |  | ⬜ 待联系 | |\n")

        f.write("\n**状态说明**:\n")
        f.write("- ⬜ 待联系\n")
        f.write("- ⏳ 已联系/等待回复\n")
        f.write("- ✅ 已安排面试\n")
        f.write("- ❌ 不合适/已拒绝\n")
        f.write("- ⭐ 已录用\n\n")

    print(f"\n✅ 报告已生成: {report_path}")
    print(f"📄 使用以下命令查看报告:")
    print(f"   cat {report_path}")
    print(f"   或打开: file://{os.path.abspath(report_path)}")

    return report_path

# ============================================================================
# 主函数
# ============================================================================
def main():
    """主流程"""
    print("🚀 紧急职位批量匹配系统 - 逐步验证版")
    print("="*80)
    print(f"配置: MIN_URGENCY={MIN_URGENCY}, TOP_K={TOP_K}, MIN_SCORE={MIN_SCORE}")
    print()
    
    # 验证点 1: 数据库
    if not verify_database():
        print("\n❌ 数据库验证失败，请修复后重试")
        return
    
    if not wait_for_verification("\n按 Enter 继续..."):
        return
    
    # 验证点 2: 数据完整性
    if not verify_data_integrity():
        print("\n❌ 数据完整性验证失败")
        return
    
    if not wait_for_verification("\n按 Enter 继续..."):
        return
    
    # 验证点 3: 向量索引
    if not verify_vector_index():
        print("\n❌ 向量索引验证失败")
        return
    
    if not wait_for_verification("\n按 Enter 继续..."):
        return
    
    # 验证点 4: 单职位测试
    if not verify_single_match():
        print("\n❌ 单职位测试失败")
        return
    
    if not wait_for_verification("\n按 Enter 继续全量匹配..."):
        return
    
    # 验证点 5: 全量匹配
    success, matched_jobs = verify_full_match()

    if success:
        print(f"\n✅ 所有验证通过！")
        print(f"\n下一步: 生成详细匹配清单")
        print()
        report_path = generate_matching_report(matched_jobs)
        print()
        print("=" * 80)
        print("🎉 紧急职位批量匹配完成！")
        print("=" * 80)
    else:
        print(f"\n⚠️  匹配完成，但质量需要改进")

if __name__ == "__main__":
    main()
