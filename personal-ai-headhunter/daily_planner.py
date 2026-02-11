#!/usr/bin/env python3
"""
Headhunter Agent-Lite — 每日工作台
🧠 Agent大脑MVP：读取数据库状态 → LLM分析 → 输出今日行动计划

用法：
  python daily_planner.py              # 运行并输出
  python daily_planner.py --no-llm     # 仅输出统计数据，不调用LLM
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from collections import Counter

# 确保项目路径正确
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

# 加载环境变量（复用现有配置）
config_env = os.path.join(BASE_DIR, 'config.env')
if os.path.exists(config_env):
    load_dotenv(config_env, override=True)
else:
    load_dotenv()

from database import SessionLocal, Candidate, Job, MatchRecord
from sqlalchemy import func, text


# ──────────────────────────────────────────────
# 步骤0：Sourcing 执行数据采集
# ──────────────────────────────────────────────

# 两周 KPI 目标 (与 sourcing_execution_plan.md 对齐)
SOURCING_TARGETS = {
    'maimai_greeting': 250,     # 脉脉打招呼总目标 (精准)
    'maimai_friend': 4000,      # 脉脉加好友总目标 (广撒网)
    'linkedin_request': 250,    # LinkedIn Connection 总目标
    'linkedin_post': 11,        # LinkedIn 帖子总目标
    'email': 150,               # Email 发送总目标
    'replies': 200,             # 全渠道回复总目标
    'referrals': 20,            # 推荐提交总目标
}


def collect_sourcing_progress():
    """从 sourcing_推进.md 解析多渠道数据追踪表"""
    sourcing_file = os.path.join(BASE_DIR, 'data', 'sourcing_推进.md')
    if not os.path.exists(sourcing_file):
        return None

    with open(sourcing_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到数据追踪表
    daily_records = []
    in_table = False
    header_found = False

    for line in content.split('\n'):
        line = line.strip()
        if '脉脉招呼' in line and '脉脉加友' in line:
            in_table = True
            header_found = False
            continue
        if in_table and line.startswith('|:'):
            header_found = True
            continue
        if in_table and header_found and line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 9:
                record = {
                    'date': cells[0],
                    'target_company': cells[1],
                    'maimai_greeting': _parse_num(cells[2]),
                    'maimai_friend': _parse_num(cells[3]),
                    'linkedin_request': _parse_num(cells[4]),
                    'linkedin_post': _parse_num(cells[5]),
                    'email': _parse_num(cells[6]),
                    'replies': _parse_num(cells[7]),
                    'referrals': _parse_num(cells[8]),
                    'notes': cells[9] if len(cells) > 9 else '',
                }
                daily_records.append(record)
        elif in_table and header_found and not line.startswith('|'):
            break

    # 计算合计
    totals = {k: 0 for k in SOURCING_TARGETS}
    days_with_data = 0
    for r in daily_records:
        has_data = False
        for key in SOURCING_TARGETS:
            val = r.get(key, 0)
            if val > 0:
                totals[key] += val
                has_data = True
        if has_data:
            days_with_data += 1

    # 找到今日目标
    today_str = datetime.now().strftime('%-m/%d')
    today_weekday = ['一', '二', '三', '四', '五', '六', '日'][datetime.now().weekday()]
    today_target = None
    for r in daily_records:
        if today_str in r['date'] or f'({today_weekday})' in r['date']:
            today_target = r
            break

    # 找到昨日数据
    yesterday_data = None
    if len(daily_records) >= 2:
        yesterday_data = daily_records[-2] if daily_records[-1] == today_target else daily_records[-1]

    return {
        'daily_records': daily_records,
        'totals': totals,
        'targets': SOURCING_TARGETS,
        'days_with_data': days_with_data,
        'today_target': today_target,
        'yesterday_data': yesterday_data,
    }


def _parse_num(val):
    """解析数字，处理空值和特殊符号"""
    if not val or val in ('—', '___', '-', ''):
        return 0
    try:
        return int(re.sub(r'[^0-9]', '', val))
    except (ValueError, TypeError):
        return 0


# ──────────────────────────────────────────────
# 步骤1：数据采集层
# ──────────────────────────────────────────────

def collect_daily_context():
    """采集当日所需的所有上下文数据"""
    session = SessionLocal()
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    try:
        # ── 候选人统计 ──
        total_candidates = session.query(func.count(Candidate.id)).scalar()
        total_friends = session.query(func.count(Candidate.id)).filter(
            Candidate.is_friend == 1
        ).scalar()
        candidates_with_tags = session.query(func.count(Candidate.id)).filter(
            Candidate.structured_tags.isnot(None),
            Candidate.structured_tags != 'null'
        ).scalar()

        # 最近7天新增候选人
        recent_candidates = session.query(Candidate).filter(
            Candidate.created_at >= week_ago
        ).order_by(Candidate.created_at.desc()).all()

        # 昨日新增候选人 + 分渠道明细
        yesterday_candidates = session.query(Candidate).filter(
            Candidate.created_at >= yesterday,
            Candidate.created_at < today
        ).all()

        yesterday_by_source = Counter()
        yesterday_tech_domains = Counter()
        for c in yesterday_candidates:
            yesterday_by_source[c.source or "未知"] += 1
            # 提取技术方向
            if c.structured_tags and isinstance(c.structured_tags, dict):
                for domain in c.structured_tags.get('tech_domain', []):
                    yesterday_tech_domains[domain] += 1
            elif c.structured_tags and isinstance(c.structured_tags, str):
                try:
                    tags = json.loads(c.structured_tags)
                    for domain in tags.get('tech_domain', []):
                        yesterday_tech_domains[domain] += 1
                except:
                    pass

        # 本周新增候选人技术分布
        week_tech_domains = Counter()
        for c in recent_candidates:
            if c.structured_tags and isinstance(c.structured_tags, dict):
                for domain in c.structured_tags.get('tech_domain', []):
                    week_tech_domains[domain] += 1
            elif c.structured_tags and isinstance(c.structured_tags, str):
                try:
                    tags = json.loads(c.structured_tags)
                    for domain in tags.get('tech_domain', []):
                        week_tech_domains[domain] += 1
                except:
                    pass

        # 本周新增候选人分渠道
        week_by_source = Counter()
        for c in recent_candidates:
            week_by_source[c.source or "未知"] += 1

        # 今天需要联系的候选人（scheduled_contact_date）
        scheduled_today = session.query(Candidate).filter(
            Candidate.scheduled_contact_date == today
        ).all()

        # 过期的预约联系（scheduled_contact_date < today 且不为空）
        overdue_scheduled = session.query(Candidate).filter(
            Candidate.scheduled_contact_date.isnot(None),
            Candidate.scheduled_contact_date < today,
            Candidate.scheduled_contact_date != ''
        ).all()

        # 已加好友但从未沟通的候选人
        friends_no_comm = session.query(Candidate).filter(
            Candidate.is_friend == 1,
            (Candidate.communication_logs.is_(None)) |
            (Candidate.communication_logs == '[]') |
            (Candidate.communication_logs == 'null')
        ).all()

        # 有过沟通但超过14天未联系的候选人
        stale_candidates = session.query(Candidate).filter(
            Candidate.last_communication_at.isnot(None),
            Candidate.last_communication_at < two_weeks_ago
        ).order_by(Candidate.last_communication_at.asc()).limit(20).all()

        # ── Pipeline 漏斗统计 ──
        pipeline_stages = {}
        stage_rows = session.query(
            Candidate.pipeline_stage, func.count(Candidate.id)
        ).group_by(Candidate.pipeline_stage).all()
        for stage, count in stage_rows:
            pipeline_stages[stage or 'new'] = count

        # 漏斗计算（累加式）
        funnel = {
            'total': total_candidates,
            'contacted': sum(pipeline_stages.get(s, 0) for s in
                           ['contacted', 'following_up', 'replied', 'wechat_connected', 'in_pipeline']),
            'replied': sum(pipeline_stages.get(s, 0) for s in
                         ['replied', 'wechat_connected', 'in_pipeline']),
            'wechat': sum(pipeline_stages.get(s, 0) for s in
                        ['wechat_connected', 'in_pipeline']),
            'in_pipeline': pipeline_stages.get('in_pipeline', 0),
        }

        # ── JD统计 ──
        total_active_jds = session.query(func.count(Job.id)).filter(
            Job.is_active == 1
        ).scalar()

        # 紧急JD（urgency >= 2）
        urgent_jds = session.query(Job).filter(
            Job.is_active == 1,
            Job.urgency >= 2
        ).order_by(Job.urgency.desc()).all()

        # 最近7天新增JD
        recent_jds = session.query(Job).filter(
            Job.is_active == 1,
            Job.created_at >= week_ago
        ).order_by(Job.created_at.desc()).all()

        # 本周新增紧急JD
        recent_urgent_jds = [j for j in recent_jds if (j.urgency or 0) >= 2]

        # 3个月内紧急JD
        urgent_jds_3m = session.query(Job).filter(
            Job.is_active == 1,
            Job.urgency >= 2,
            Job.created_at >= three_months_ago
        ).all()

        # JD的匹配记录统计
        jd_match_counts = dict(
            session.query(MatchRecord.job_id, func.count(MatchRecord.id))
            .group_by(MatchRecord.job_id).all()
        )

        # 没有任何匹配记录的活跃JD（管道为空）
        all_active_jds = session.query(Job).filter(Job.is_active == 1).all()
        jds_no_pipeline = [j for j in all_active_jds if j.id not in jd_match_counts]

        # JD按公司分布
        company_counts = Counter()
        for j in all_active_jds:
            company_counts[j.company or "未知"] += 1

        # ── 候选人来源分布 ──
        source_counts = Counter()
        all_candidates_sources = session.query(Candidate.source).all()
        for (src,) in all_candidates_sources:
            source_counts[src or "未知"] += 1

        return {
            "date": today,
            "stats": {
                "total_candidates": total_candidates,
                "total_friends": total_friends,
                "candidates_with_tags": candidates_with_tags,
                "total_active_jds": total_active_jds,
                "recent_candidates_count": len(recent_candidates),
                "recent_jds_count": len(recent_jds),
                "urgent_jds_count": len(urgent_jds),
                "recent_urgent_jds_count": len(recent_urgent_jds),
                "urgent_jds_3m_count": len(urgent_jds_3m),
                "jds_no_pipeline_count": len(jds_no_pipeline),
                "friends_no_comm_count": len(friends_no_comm),
                "yesterday_count": len(yesterday_candidates),
            },
            # 昨日分渠道
            "yesterday_by_source": dict(yesterday_by_source.most_common(10)),
            "yesterday_tech_domains": dict(yesterday_tech_domains.most_common(10)),
            # 本周分渠道 & 技术分布
            "week_by_source": dict(week_by_source.most_common(10)),
            "week_tech_domains": dict(week_tech_domains.most_common(10)),
            # Pipeline 漏斗
            "pipeline_stages": pipeline_stages,
            "funnel": funnel,
            "scheduled_today": [
                {"name": c.name, "company": c.current_company, "title": c.current_title,
                 "scheduled_date": c.scheduled_contact_date}
                for c in scheduled_today
            ],
            "overdue_scheduled": [
                {"name": c.name, "company": c.current_company, "title": c.current_title,
                 "scheduled_date": c.scheduled_contact_date}
                for c in overdue_scheduled[:10]  # 最多显示10个
            ],
            "urgent_jds": [
                {"id": j.id, "title": j.title, "company": j.company,
                 "urgency": j.urgency, "headcount": j.headcount,
                 "job_code": j.job_code}
                for j in urgent_jds[:10]
            ],
            "recent_jds": [
                {"id": j.id, "title": j.title, "company": j.company,
                 "job_code": j.job_code,
                 "created_at": j.created_at.strftime("%m-%d") if j.created_at else ""}
                for j in recent_jds[:10]
            ],
            "jds_no_pipeline_sample": [
                {"id": j.id, "title": j.title, "company": j.company,
                 "urgency": j.urgency, "job_code": j.job_code}
                for j in sorted(jds_no_pipeline, key=lambda x: x.urgency or 0, reverse=True)[:15]
            ],
            "stale_candidates": [
                {"name": c.name, "company": c.current_company, "title": c.current_title,
                 "last_comm": c.last_communication_at.strftime("%Y-%m-%d") if c.last_communication_at else ""}
                for c in stale_candidates[:10]
            ],
            "recent_candidates": [
                {"name": c.name, "company": c.current_company, "title": c.current_title,
                 "source": c.source,
                 "created_at": c.created_at.strftime("%m-%d") if c.created_at else ""}
                for c in recent_candidates[:10]
            ],
            "company_distribution": dict(company_counts.most_common(10)),
            "source_distribution": dict(source_counts.most_common(10)),
            "sourcing_progress": collect_sourcing_progress(),
        }
    finally:
        session.close()


# ──────────────────────────────────────────────
# 步骤2：LLM分析层
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """你是Lillian的AI猎头助手。分析数据库状态并生成今日行动计划。

输出JSON格式如下，high_priority必须有1-3个完整的对象，suggested必须有1-3个完整的对象：

```json
{
    "greeting": "包含日期的一句话问候",
    "high_priority": [
        {"action": "跟进徐学欣等5位过期未联系候选人", "reason": "预约日期已过期2-3天", "how": "优先联系徐学欣和王越"},
        {"action": "为MiniMax紧急JD启动sourcing", "reason": "6个紧急JD管道全空HC合计36", "how": "脉脉按竞对公司搜索AI Infra方向"}
    ],
    "suggested": [
        {"action": "批量匹配本周新增130位候选人", "reason": "778个JD管道为空需建立匹配"}
    ],
    "pipeline_health": "778个活跃JD管道全空急需建立匹配",
    "weekly_insight": "本周新增130候选人336个JD数据充足但匹配滞后"
}
```

规则：引用具体的候选人名字和JD标题，用中文。"""


def generate_plan_with_llm(context: dict) -> dict:
    """调用 Qwen-max 生成行动计划"""
    import re
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    model = os.getenv("MODEL_NAME", "qwen-max")

    # 精简context，只传关键数据给LLM（节省token）
    llm_context = {
        "今日日期": context["date"],
        "数据概览": context["stats"],
        "今日预约联系": context["scheduled_today"],
        "过期未联系": context["overdue_scheduled"],
        "紧急JD": context["urgent_jds"],
        "本周新增JD": context["recent_jds"],
        "管道为空的JD（按紧急度排序前15）": context["jds_no_pipeline_sample"],
        "超期未跟进候选人": context["stale_candidates"],
        "本周新增候选人": context["recent_candidates"],
        "JD公司分布Top10": context["company_distribution"],
    }

    user_content = f"""请分析以下数据库状态，生成今日行动计划。

{json.dumps(llm_context, ensure_ascii=False, indent=2)}

请返回JSON，high_priority和suggested中每个对象都必须有完整的字段值。"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            timeout=60
        )
        content = response.choices[0].message.content

        # 从返回中提取JSON（可能包含markdown代码块）
        json_str = content
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
        else:
            # 尝试找到 { ... } 块
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = content[start:end + 1]

        plan = json.loads(json_str)

        # 兼容处理：如果数组里有空dict，过滤掉
        if "high_priority" in plan:
            plan["high_priority"] = [
                item for item in plan["high_priority"]
                if isinstance(item, dict) and item
            ]
        if "suggested" in plan:
            plan["suggested"] = [
                item for item in plan["suggested"]
                if isinstance(item, dict) and item
            ]

        return plan
    except Exception as e:
        print(f"❌ LLM调用失败: {e}")
        print(f"❌ 原始返回: {content[:1000] if 'content' in dir() else 'N/A'}")
        return None


# ──────────────────────────────────────────────
# 步骤3：格式化输出
# ──────────────────────────────────────────────

def format_terminal_output(context: dict, plan: dict = None):
    """终端彩色输出"""
    stats = context["stats"]
    date = context["date"]

    print("\n" + "=" * 60)
    print(f"  📋 Headhunter Agent — 每日工作台")
    print(f"  📅 {date}")
    print("=" * 60)

    # ── 数据看板 ──
    print(f"\n📊 数据看板")
    print(f"  候选人: {stats['total_candidates']} 人 "
          f"（好友 {stats['total_friends']} | "
          f"有标签 {stats['candidates_with_tags']}）")
    print(f"  活跃JD: {stats['total_active_jds']} 个 "
          f"（紧急 {stats['urgent_jds_count']} | "
          f"管道为空 {stats['jds_no_pipeline_count']}）")
    print(f"  本周新增: 候选人 {stats['recent_candidates_count']} | "
          f"JD {stats['recent_jds_count']}")
    print(f"  待跟进: 好友未沟通 {stats['friends_no_comm_count']}")

    # ── 今日预约 ──
    if context["scheduled_today"]:
        print(f"\n📞 今日预约联系（{len(context['scheduled_today'])}人）")
        for c in context["scheduled_today"]:
            print(f"  • {c['name']} — {c['company'] or ''} {c['title'] or ''}")

    # ── 过期预约 ──
    if context["overdue_scheduled"]:
        print(f"\n⚠️ 过期未联系（{len(context['overdue_scheduled'])}人）")
        for c in context["overdue_scheduled"][:5]:
            print(f"  • {c['name']} — 预约{c['scheduled_date']}，已过期")

    # ── 紧急JD ──
    if context["urgent_jds"]:
        print(f"\n🔥 紧急JD（urgency≥2）")
        for j in context["urgent_jds"][:5]:
            urgency_icon = "🔴" * min(j["urgency"], 3)
            hc = f" HC:{j['headcount']}" if j.get("headcount") else ""
            code = f" [{j['job_code']}]" if j.get("job_code") else ""
            print(f"  {urgency_icon} {j['title']} — {j['company']}{code}{hc}")

    # ── JD公司分布 ──
    if context["company_distribution"]:
        print(f"\n🏢 JD公司分布（Top 10）")
        for company, count in list(context["company_distribution"].items())[:10]:
            bar = "█" * min(count, 30) + f" {count}"
            print(f"  {company:12s} {bar}")

    # ── LLM行动计划 ──
    if plan:
        print(f"\n{'─' * 60}")
        if plan.get("greeting"):
            print(f"\n💬 {plan['greeting']}")

        high = plan.get("high_priority", [])
        if high and isinstance(high, list):
            print(f"\n🔴 今日必做")
            for i, item in enumerate(high, 1):
                if not isinstance(item, dict) or not item:
                    continue
                action = item.get('action', item.get('title', str(item)))
                reason = item.get('reason', item.get('description', ''))
                how = item.get('how', item.get('steps', ''))
                print(f"\n  {i}. {action}")
                if reason:
                    print(f"     原因: {reason}")
                if how:
                    print(f"     方法: {how}")

        suggested = plan.get("suggested", [])
        if suggested and isinstance(suggested, list):
            print(f"\n🟡 建议做")
            for i, item in enumerate(suggested, 1):
                if not isinstance(item, dict) or not item:
                    continue
                action = item.get('action', item.get('title', str(item)))
                reason = item.get('reason', item.get('description', ''))
                print(f"  {i}. {action}")
                if reason:
                    print(f"     原因: {reason}")

        if plan.get("pipeline_health"):
            print(f"\n📈 管道健康度: {plan['pipeline_health']}")

        if plan.get("weekly_insight"):
            print(f"\n💡 本周洞察: {plan['weekly_insight']}")

    # ── Sourcing 进度 ──
    sp = context.get("sourcing_progress")
    if sp:
        print(f"\n{'─' * 60}")
        print(f"\n📈 Sourcing 进度")
        totals = sp['totals']
        targets = sp['targets']

        def _bar(done, goal):
            pct = (done / goal * 100) if goal > 0 else 0
            filled = int(pct / 5)  # 20格满
            bar = '█' * min(filled, 20) + '░' * (20 - min(filled, 20))
            return f"{bar} {done}/{goal} ({pct:.0f}%)"

        print(f"  脉脉打招呼 {_bar(totals['maimai_greeting'], targets['maimai_greeting'])}")
        print(f"  脉脉加好友 {_bar(totals['maimai_friend'], targets['maimai_friend'])}")
        print(f"  LinkedIn   {_bar(totals['linkedin_request'], targets['linkedin_request'])}")
        print(f"  Email      {_bar(totals['email'], targets['email'])}")
        print(f"  全渠道回复 {_bar(totals['replies'], targets['replies'])}")
        print(f"  推荐提交   {_bar(totals['referrals'], targets['referrals'])}")

        today = sp.get('today_target')
        if today:
            print(f"\n  🎯 今日目标: {today['target_company']}")

        yesterday = sp.get('yesterday_data')
        if yesterday and yesterday.get('target_company'):
            yd_total = sum([
                yesterday.get('maimai_greeting', 0),
                yesterday.get('maimai_friend', 0),
                yesterday.get('linkedin_request', 0),
                yesterday.get('email', 0),
            ])
            if yd_total > 0:
                print(f"  📊 昨日({yesterday['target_company']}): "
                      f"脉脉招呼{yesterday.get('maimai_greeting', 0)} "
                      f"加友{yesterday.get('maimai_friend', 0)} "
                      f"LI{yesterday.get('linkedin_request', 0)} "
                      f"Email{yesterday.get('email', 0)} "
                      f"回复{yesterday.get('replies', 0)}")

    print(f"\n{'=' * 60}\n")


def save_daily_report(context: dict, plan: dict = None):
    """保存为Markdown文件"""
    date = context["date"]
    stats = context["stats"]
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    filepath = os.path.join(reports_dir, f"daily_plan_{date}.md")

    lines = [
        f"# Headhunter Agent — 每日工作台",
        f"**日期**: {date}",
        "",
        "## 📊 数据看板",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 候选人总数 | {stats['total_candidates']} |",
        f"| 已加好友 | {stats['total_friends']} |",
        f"| 有结构化标签 | {stats['candidates_with_tags']} |",
        f"| 活跃JD | {stats['total_active_jds']} |",
        f"| 紧急JD | {stats['urgent_jds_count']} |",
        f"| 管道为空JD | {stats['jds_no_pipeline_count']} |",
        f"| 好友未沟通 | {stats['friends_no_comm_count']} |",
        f"| 本周新增候选人 | {stats['recent_candidates_count']} |",
        f"| 本周新增JD | {stats['recent_jds_count']} |",
        "",
    ]

    if context["scheduled_today"]:
        lines.append("## 📞 今日预约联系")
        lines.append("")
        for c in context["scheduled_today"]:
            lines.append(f"- **{c['name']}** — {c['company'] or ''} {c['title'] or ''}")
        lines.append("")

    if context["overdue_scheduled"]:
        lines.append("## ⚠️ 过期未联系")
        lines.append("")
        for c in context["overdue_scheduled"]:
            lines.append(f"- **{c['name']}** — 预约{c['scheduled_date']}，已过期")
        lines.append("")

    if context["urgent_jds"]:
        lines.append("## 🔥 紧急JD")
        lines.append("")
        for j in context["urgent_jds"]:
            hc = f" (HC:{j['headcount']})" if j.get("headcount") else ""
            code = f" [{j['job_code']}]" if j.get("job_code") else ""
            lines.append(f"- **{j['title']}** — {j['company']}{code}{hc} — urgency:{j['urgency']}")
        lines.append("")

    if plan:
        lines.append("---")
        lines.append("")
        if plan.get("greeting"):
            lines.append(f"> {plan['greeting']}")
            lines.append("")

        high = plan.get("high_priority", [])
        if high and isinstance(high, list):
            lines.append("## 🔴 今日必做")
            lines.append("")
            for i, item in enumerate(high, 1):
                if not isinstance(item, dict) or not item:
                    continue
                action = item.get('action', item.get('title', str(item)))
                reason = item.get('reason', item.get('description', ''))
                how = item.get('how', item.get('steps', ''))
                lines.append(f"### {i}. {action}")
                if reason:
                    lines.append(f"- **原因**: {reason}")
                if how:
                    lines.append(f"- **方法**: {how}")
                lines.append("")

        suggested = plan.get("suggested", [])
        if suggested and isinstance(suggested, list):
            lines.append("## 🟡 建议做")
            lines.append("")
            for i, item in enumerate(suggested, 1):
                if not isinstance(item, dict) or not item:
                    continue
                action = item.get('action', item.get('title', str(item)))
                reason = item.get('reason', item.get('description', ''))
                lines.append(f"{i}. **{action}**{' — ' + reason if reason else ''}")
            lines.append("")

        if plan.get("pipeline_health"):
            lines.append(f"## 📈 管道健康度")
            lines.append(f"{plan['pipeline_health']}")
            lines.append("")

        if plan.get("weekly_insight"):
            lines.append(f"## 💡 本周洞察")
            lines.append(f"{plan['weekly_insight']}")
            lines.append("")

    # ── Sourcing 进度 ──
    sp = context.get("sourcing_progress")
    if sp:
        lines.append("---")
        lines.append("")
        lines.append("## 📈 Sourcing 进度")
        lines.append("")
        totals = sp['totals']
        targets = sp['targets']
        lines.append("| 渠道 | 完成 | 目标 | 进度 |")
        lines.append("|:---|:---:|:---:|:---:|")
        channel_names = {
            'maimai_greeting': '脉脉打招呼',
            'maimai_friend': '脉脉加好友',
            'linkedin_request': 'LinkedIn',
            'email': 'Email',
            'replies': '全渠道回复',
            'referrals': '推荐提交',
        }
        for key, name in channel_names.items():
            done = totals.get(key, 0)
            goal = targets.get(key, 0)
            pct = f"{done/goal*100:.0f}%" if goal > 0 else "—"
            lines.append(f"| {name} | {done} | {goal} | {pct} |")
        lines.append("")

        today = sp.get('today_target')
        if today:
            lines.append(f"**🎯 今日目标**: {today['target_company']}")
            lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

def main():
    no_llm = "--no-llm" in sys.argv

    print("🔍 正在采集数据库状态...")
    context = collect_daily_context()
    print(f"✅ 数据采集完成")

    plan = None
    if not no_llm:
        print("🧠 正在调用 LLM 分析生成行动计划...")
        plan = generate_plan_with_llm(context)
        if plan:
            print("✅ 行动计划生成完成")
        else:
            print("⚠️ LLM分析失败，仅输出统计数据")

    # 终端输出
    format_terminal_output(context, plan)

    # 保存报告
    filepath = save_daily_report(context, plan)
    print(f"📄 报告已保存: {filepath}")


if __name__ == "__main__":
    main()
