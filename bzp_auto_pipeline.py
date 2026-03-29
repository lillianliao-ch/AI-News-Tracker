import os
import json
import time
import random
import argparse
import subprocess
import urllib.request
from typing import List, Dict

# Try to load .env, but won't fail if missing.
try:
    from dotenv import load_dotenv
    load_dotenv("/Users/lillianliao/notion_rag/.env")
except ImportError:
    pass

class QwenEngine:
    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-4e2bb9108e1541f9b7dd88855922c7a3")

    def call_qwen(self, prompt: str) -> str:
        data = {
            "model": "qwen-plus",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        req = urllib.request.Request(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            data=json.dumps(data).encode('utf-8'),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"❌ LLM API 故障: {e}")
            return "您好，您的背景很棒，我们目前有大模型相关的优质机会想要交流一下，有兴趣深入聊聊吗？"

def generate_greeting(candidate: Dict, qwen: QwenEngine) -> str:
    name = candidate.get("name", "牛人")
    labels = candidate.get("labels", "")
    if isinstance(labels, list):
        labels_str = " / ".join(labels)
    else:
        labels_str = str(labels)
    
    prompt = f"""你是一个高级AI行业猎头专家。正在为Boss直聘上的一位候选人打招呼。
候选人信息:
- 姓名(或称呼): {name}
- 标签与履历关键字: {labels_str}

请你写一段非常简短、专业、定制化且有诚意的寒暄(1-2句话以内)。
如果你看到顶级学历(如清华北大多伦多)或顶级大厂(如阿里字节)，请稍微提及来拉近关系。
只输出打招呼的纯文本，不要包含任何多余内容、引号或解释。"""
    
    msg = qwen.call_qwen(prompt)
    return msg

def run_cmd(cmd: List[str], dry_run: bool = False, capture: bool = False):
    if dry_run:
        print(f"[DRY-RUN] 执行命令: {' '.join(cmd)}")
        if capture:
            # Return dummy json for test
            if "recommend" in cmd:
                return '[{"encrypt_uid":"boss_123","name":"张三","labels":["某大厂","清华大学","大模型底层开发"]}]'
            return ""
        return
    
    print(f"🚀 执行命令: {' '.join(cmd)}")
    try:
        if capture:
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return res.stdout
        else:
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e.cmd}")
        print(f"   返回码: {e.returncode}")
        if capture:
            print(f"   输出: {e.output}")
        raise

def phase_1(dry_run: bool):
    print("--- [ Phase 1: Recommend & Greet ] ---")
    # 注意：招聘端(B端)找牛人必须用 recommend 命令获取系统推荐列表，而不是 search(C端求职用)
    search_cmd = ["npx", "--yes", "@jackwener/opencli", "boss", "recommend", "--format", "json"]
    
    stdout = run_cmd(search_cmd, dry_run=dry_run, capture=True)
    
    candidates = []
    try:
        if stdout:
            candidates = json.loads(stdout)
    except json.JSONDecodeError:
        print("⚠️ 无法解析 Boss 直聘的返回结果为 JSON。")
        return

    if not candidates:
        print("未找到任何候选人。")
        return

    print(f"✅ 找到 {len(candidates)} 名候选人。")
    
    qwen = QwenEngine()
    processed_ids = []

    for c in candidates:
        # B端的唯一标识符叫做 encrypt_uid
        cid = c.get("encrypt_uid")
        sec_id = c.get("security_id")
        job_id = c.get("encrypt_job_id")
        
        if not cid or not sec_id:
            continue
            
        print(f"\n>> 正在处理候选人: {c.get('name', 'Unknown')}")
        greeting = generate_greeting(c, qwen)
        print(f"> Qwen 生成问候语: {greeting}")
        
        greet_cmd = [
            "npx", "--yes", "@jackwener/opencli", "boss", "greet", str(cid),
            "--security-id", str(sec_id),
            "--text", greeting
        ]
        if job_id:
            greet_cmd.extend(["--job-id", str(job_id)])
            
        run_cmd(greet_cmd, dry_run=dry_run)
        
        processed_ids.append(cid)
        
        if not dry_run:
            # 防封休眠策略
            sleep_time = random.uniform(15.0, 45.0)
            print(f"💤 休眠 {sleep_time:.2f} 秒以防挂机封号...")
            time.sleep(sleep_time)

    # 保存到队列以供 Phase 2 使用
    with open("bzp_queue.json", "w") as f:
        json.dump(processed_ids, f)
    print("✅ Phase 1 结束。候选人 ID 已保存至 bzp_queue.json。")


def phase_2(dry_run: bool):
    print("--- [ Phase 2: Exchange & CRM ] ---")
    if not os.path.exists("bzp_queue.json"):
        print("⚠️ 找不到 bzp_queue.json，请先执行 Phase 1。")
        return
        
    with open("bzp_queue.json", "r") as f:
        queue = json.load(f)

    print(f"✅ 从队列中读取到 {len(queue)} 个等待交换联系方式的 ID。")
    
    for cid in queue:
        print(f"\n>> 请求交换联系方式 + 录入 CRM，针对 ID: {cid}")
        # 请求微信
        exchange_cmd = ["npx", "--yes", "@jackwener/opencli", "boss", "exchange", str(cid), "--type", "wechat"]
        run_cmd(exchange_cmd, dry_run=dry_run)
        
        # 录入飞书
        # Note: Replace placeholders with your actual Feishu CRM spreadsheet references.
        lark_cmd = [
            "npx", "--yes", "@jackwener/opencli", "lark-cli", "spreadsheets", "insert",
            "--id", "REPLACE_WITH_SPREADSHEET_TOKEN",
            "--range", "REPLACE_WITH_SHEET_ID",
            "--values", f"{cid},Boss交换中,等待回复"
        ]
        run_cmd(lark_cmd, dry_run=dry_run)
        
        if not dry_run:
            sleep_time = random.uniform(20.0, 50.0)
            print(f"💤 休眠 {sleep_time:.2f} 秒以防挂机封号...")
            time.sleep(sleep_time)
            
    # 执行完后清理队列 (可选)
    # os.remove("bzp_queue.json")
    print("✅ Phase 2 结束。")

def main():
    parser = argparse.ArgumentParser(description="Boss Zhipin Auto Pipeline (OpenCLI)")
    parser.add_argument("--phase", type=int, choices=[1, 2], required=True, help="1: Search&Greet, 2: Exchange&CRM")
    parser.add_argument("--dry-run", action="store_true", help="只打印命令，不会真正调用 Boss 直聘")
    
    args = parser.parse_args()
    
    if args.phase == 1:
        phase_1(args.dry_run)
    elif args.phase == 2:
        phase_2(args.dry_run)

if __name__ == "__main__":
    main()
