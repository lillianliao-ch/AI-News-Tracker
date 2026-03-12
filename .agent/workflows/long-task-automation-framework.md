---
description: 通用长时间任务自动化执行框架，支持断点续传、自动重启、进度追踪
---

# 长时间任务自动化执行框架

> 🎯 **目标**: 解决 AI Agent 执行长时间任务时的问题：
> - 会话长度限制（Token 限制）
> - 网络中断导致任务失败
> - API 速率限制需要等待
> - 需要人工监控进度
> - 任务失败后难以恢复

---

## 📋 框架设计原则

### 1. 状态可持久化
- 所有进度保存到文件/数据库
- 任意时刻可恢复，不丢失数据
- 支持断点续传

### 2. 任务原子化
- 大任务分解为小步骤
- 每个步骤可独立执行
- 失败后可从失败点恢复

### 3. 自动重启机制
- 任务失败自动重启
- 网络错误自动重试
- API 限制自动等待

### 4. 进度可观测
- 实时日志输出
- 进度文件可查询
- 支持外部监控

---

## 🏗️ 框架架构

```
┌─────────────────────────────────────────────────────┐
│              Task Coordinator (任务协调器)            │
│  - 读取任务配置                                       │
│  - 检查断点状态                                       │
│  - 分发子任务                                         │
└──────────────────┬──────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       │                       │
┌──────▼──────┐        ┌──────▼──────┐
│ Task Runner │        │ State Store │
│ - 执行任务   │        │ - 保存状态   │
│ - 错误处理   │◀───────│ - 进度追踪   │
│ - 自动重试   │        │ - 断点恢复   │
└──────┬──────┘        └─────────────┘
       │
┌──────▼──────┐
│   Monitor   │
│ - 日志输出   │
│ - 进度报告   │
│ - 告警通知   │
└─────────────┘
```

---

## 📦 核心组件

### 1. Task Coordinator（任务协调器）

```python
# framework/task_coordinator.py
import json
import time
from pathlib import Path
from typing import Dict, List, Callable, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TaskCoordinator:
    """
    通用任务协调器

    功能：
    1. 任务定义和依赖管理
    2. 断点续传
    3. 自动重启
    4. 进度追踪
    """

    def __init__(self, task_name: str, work_dir: Path = Path("./tasks")):
        self.task_name = task_name
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 状态文件
        self.state_file = self.work_dir / f"{task_name}_state.json"
        self.log_file = self.work_dir / f"{task_name}.log"
        self.progress_file = self.work_dir / f"{task_name}_progress.json"

        # 加载状态
        self.state = self._load_state()
        self.tasks: List[Dict] = []

    def define_task(self,
                   task_id: str,
                   executor: Callable,
                   dependencies: List[str] = None,
                   retry: int = 3,
                   timeout: int = 3600):
        """
        定义一个任务

        Args:
            task_id: 任务唯一标识
            executor: 执行函数，签名为 executor(context) -> bool
            dependencies: 依赖的任务ID列表
            retry: 失败重试次数
            timeout: 超时时间（秒）
        """
        self.tasks.append({
            "id": task_id,
            "executor": executor,
            "dependencies": dependencies or [],
            "retry": retry,
            "timeout": timeout,
            "status": TaskStatus.PENDING,
            "result": None,
            "error": None,
            "started_at": None,
            "completed_at": None,
        })

    def run(self, auto_restart: bool = True):
        """
        执行所有任务

        Args:
            auto_restart: 失败后是否自动重启整个流程
        """
        while True:
            try:
                self._execute_all_tasks()
                if auto_restart:
                    self.log("✅ 所有任务完成！")
                    break
                return

            except KeyboardInterrupt:
                self.log("⚠️  用户中断")
                self._save_state()
                raise

            except Exception as e:
                self.log(f"❌ 执行失败: {str(e)}")

                if auto_restart:
                    self.log("🔄 30秒后自动重启...")
                    time.sleep(30)
                    continue
                else:
                    raise

    def _execute_all_tasks(self):
        """执行所有任务（支持断点续传）"""
        # 构建任务依赖图
        task_map = {t["id"]: t for t in self.tasks}

        # 按依赖顺序执行
        executed = set()
        for task in self.tasks:
            self._execute_task(task, task_map, executed)

    def _execute_task(self, task: Dict, task_map: Dict, executed: set):
        """执行单个任务（递归处理依赖）"""
        task_id = task["id"]

        # 已完成则跳过
        if task_id in executed:
            return

        # 检查断点状态
        if self.state.get(task_id, {}).get("status") == TaskStatus.COMPLETED.value:
            self.log(f"⏭️  跳过已完成任务: {task_id}")
            executed.add(task_id)
            return

        # 先执行依赖任务
        for dep_id in task["dependencies"]:
            if dep_id not in executed:
                dep_task = task_map.get(dep_id)
                if dep_task:
                    self._execute_task(dep_task, task_map, executed)

        # 执行当前任务
        self._run_task_with_retry(task)
        executed.add(task_id)

    def _run_task_with_retry(self, task: Dict):
        """执行任务并支持重试"""
        task_id = task["id"]
        retry_count = 0
        max_retry = task["retry"]

        while retry_count <= max_retry:
            try:
                self.log(f"🚀 执行任务: {task_id} (尝试 {retry_count + 1}/{max_retry + 1})")

                # 更新状态
                task["status"] = TaskStatus.RUNNING
                task["started_at"] = datetime.now().isoformat()
                self._update_task_state(task_id, task)
                self._save_state()

                # 创建任务上下文
                context = {
                    "task_id": task_id,
                    "work_dir": self.work_dir,
                    "state": self.state,
                    "log": self.log
                }

                # 执行任务
                result = task["executor"](context)

                # 成功
                task["status"] = TaskStatus.COMPLETED
                task["result"] = result
                task["completed_at"] = datetime.now().isoformat()
                self._update_task_state(task_id, task)
                self._save_state()
                self.log(f"✅ 任务完成: {task_id}")
                return

            except Exception as e:
                retry_count += 1
                task["error"] = str(e)
                self._update_task_state(task_id, task)
                self._save_state()

                if retry_count <= max_retry:
                    wait_time = min(60 * retry_count, 300)  # 最多等待5分钟
                    self.log(f"⚠️  任务失败，{wait_time}秒后重试: {str(e)}")
                    time.sleep(wait_time)
                else:
                    task["status"] = TaskStatus.FAILED
                    self._save_state()
                    self.log(f"❌ 任务失败（已达最大重试次数）: {task_id}")
                    raise

    def _load_state(self) -> Dict:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_state(self):
        """保存状态"""
        # 保存完整状态
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

        # 保存可读进度
        progress = self._generate_progress_report()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    def _update_task_state(self, task_id: str, task: Dict):
        """更新单个任务状态"""
        self.state[task_id] = {
            "status": task["status"].value,
            "started_at": task.get("started_at"),
            "completed_at": task.get("completed_at"),
            "error": task.get("error"),
            "result": str(task.get("result"))[:200] if task.get("result") else None
        }

    def _generate_progress_report(self) -> Dict:
        """生成进度报告"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t["status"] == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t["status"] == TaskStatus.FAILED)
        running = sum(1 for t in self.tasks if t["status"] == TaskStatus.RUNNING)

        return {
            "task_name": self.task_name,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "progress_percentage": round(completed / total * 100, 2) if total > 0 else 0,
            "tasks": [
                {
                    "id": t["id"],
                    "status": t["status"].value,
                    "started_at": t.get("started_at"),
                    "completed_at": t.get("completed_at"),
                    "error": t.get("error")
                }
                for t in self.tasks
            ]
        }

    def log(self, message: str):
        """日志输出"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line, flush=True)

        # 写入日志文件
        with open(self.log_file, 'a') as f:
            f.write(log_line + "\n")

    def get_progress(self) -> Dict:
        """获取当前进度"""
        return self._generate_progress_report()
```

---

### 2. Auto Restart Wrapper（自动重启包装器）

```python
# framework/auto_restart.py
import subprocess
import time
import sys
from pathlib import Path

class AutoRestartWrapper:
    """
    自动重启包装器

    用法：
    1. 在主脚本最后添加：
       if __name__ == "__main__":
           AutoRestartWrapper.run(main_function)

    2. 或使用装饰器：
       @AutoRestartWrapper.wrap
       def main():
           ...
    """

    @staticmethod
    def run(main_func, max_restarts: int = 100, restart_delay: int = 30):
        """
        运行主函数，失败后自动重启

        Args:
            main_func: 主函数
            max_restarts: 最大重启次数
            restart_delay: 重启延迟（秒）
        """
        restart_count = 0

        while restart_count < max_restarts:
            try:
                main_func()
                break  # 成功完成，退出

            except KeyboardInterrupt:
                print("⚠️  用户中断，退出")
                break

            except Exception as e:
                restart_count += 1
                print(f"❌ 执行失败 (第 {restart_count} 次): {str(e)}")

                if restart_count < max_restarts:
                    print(f"🔄 {restart_delay}秒后自动重启...")
                    time.sleep(restart_delay)
                else:
                    print(f"❌ 达到最大重启次数，退出")
                    raise

    @staticmethod
    def wrap(max_restarts: int = 100):
        """
        装饰器版本
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                return AutoRestartWrapper.run(func, max_restarts)
            return wrapper
        return decorator
```

---

### 3. Progress Monitor（进度监控）— 视觉化规范

> 🎯 所有批量脚本必须配套 `check_progress.sh` 监控器，使用统一的进度条风格。

#### 输出规范

所有监控器的终端输出必须遵循以下格式：

```
═══════════════════════════════════════════════════
  📊 Mining Progress Monitor  (Ctrl+C to exit)
═══════════════════════════════════════════════════
  ⏰ 18:08:28

  🔬 GitHub Mining — phase5_full_production_final
     15,472 candidates | running 7h22m

     Phase 3   S2学术富化    [████████████████████░░░░░░░░░░]  67.8%  10,497/15,472
                                  23.7/min  ETA 21:38
     Phase 3.5 网络挖掘      [████████████████████░░░░░░░░░░]  67.8%  10,497/15,472
                                  23.7/min  ETA 21:38
     Phase 4.5 LLM深度富化   [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   waiting...

  🔧 Processes: network_miner(phase3.5), batch_runner

  💡 Tip: bash check_progress.sh -w  ← 实时刷新模式
```

#### 核心元素

| 元素 | 说明 | 必须 |
|------|------|:----:|
| 进度条 `[█░]` | 30字符宽，`█` 填充 `░` 空白 | ✅ |
| 百分比 | 右对齐 `XX.X%` | ✅ |
| 计数 | `已完成/总数` 带千分位逗号 | ✅ |
| 速率 | `XX.X/min` | ✅ |
| ETA | 预计完成时间 `HH:MM` | ✅ |
| 阶段状态 | `✅ Done` / `🔄 运行中` / `⏳ 等待中` | ✅ |
| 活跃进程 | 通过 `ps` 检测，一行列出 | ✅ |
| Watch 模式 | `-w` 参数，每 10 秒 `clear` + 重绘 | ✅ |

#### Shell 模板

```bash
#!/bin/bash
# {任务名} 进度监控
# 用法: bash check_progress.sh        (单次)
#       bash check_progress.sh -w     (实时刷新)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WATCH_MODE=false
[[ "$1" == "-w" || "$1" == "--watch" ]] && WATCH_MODE=true

show_progress() {
python3 << 'PYTHON'
import json, os, subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ── 进度条工具函数 ──
def bar(pct, width=30):
    filled = int(width * pct / 100)
    return f"[{'█' * filled}{'░' * (width - filled)}]"

def fmt_dur(m):
    if m < 60: return f"{m:.0f}m"
    h, m = divmod(int(m), 60)
    return f"{h}h{m:02d}m"

now = datetime.now()
print(f"  ⏰ {now.strftime('%H:%M:%S')}")
print()

# ── 读取数据、计算进度 ──
# TODO: 替换为实际文件路径和总量
total = 10000
processed = 0  # len(json.load(open(progress_file)))
pct = processed / total * 100 if total else 0

# elapsed = (now - start_time).total_seconds() / 60
# speed = processed / elapsed if elapsed > 0 else 0
# remaining = (total - processed) / speed if speed > 0 and processed < total else 0
# eta = now + timedelta(minutes=remaining)

# ── 输出进度条 ──
# print(f"     Phase 1  任务描述  {bar(pct)} {pct:5.1f}%  {processed:,}/{total:,}")
# print(f"     {'':25s}  {speed:.1f}/min  ETA {eta.strftime('%H:%M')}")

# ── 检测活跃进程 ──
res = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
procs = []
for l in res.stdout.split('\n'):
    if 'grep' in l or 'check_progress' in l: continue
    # if 'your_process_name' in l: procs.append("your_process")
status = ", ".join(procs) if procs else "⏸️ idle"
print(f"  🔧 Processes: {status}")
PYTHON
}

if $WATCH_MODE; then
    while true; do
        clear
        echo "═══════════════════════════════════════════════════"
        echo "  📊 {任务名} Progress Monitor  (Ctrl+C to exit)"
        echo "═══════════════════════════════════════════════════"
        show_progress
        sleep 10
    done
else
    echo "═══════════════════════════════════════════════════"
    echo "  📊 {任务名} Progress"
    echo "═══════════════════════════════════════════════════"
    show_progress
    echo ""
    echo "  💡 Tip: bash check_progress.sh -w  ← 实时刷新模式"
fi
```

#### 命名规范

| 文件 | 位置 | 说明 |
|------|------|------|
| `check_progress.sh` | 与批量脚本同目录 | 固定文件名 |
| 单次运行 | `bash check_progress.sh` | 打印一次后退出 |
| Watch 模式 | `bash check_progress.sh -w` | 每 10s 自动刷新 |

#### 实际示例

参考 GitHub Mining 的 `check_progress.sh`：
[check_progress.sh](file:///Users/lillianliao/notion_rag/github_mining/scripts/check_progress.sh)

---

## 🚀 使用示例

### 示例 1: GitHub Mining 任务

```python
# tasks/github_mining_task.py
from framework.task_coordinator import TaskCoordinator
from framework.auto_restart import AutoRestartWrapper
import requests
import json

def step1_extract_seeds(context):
    """步骤1: 提取种子"""
    print("正在从数据库提取 S/A+/A 级种子...")

    # 实际逻辑...
    seeds = [{"username": "jindongwang", "tier": "S"}]

    # 保存结果
    output_file = context["work_dir"] / "seeds.json"
    with open(output_file, 'w') as f:
        json.dump(seeds, f)

    return {"seed_count": len(seeds)}

def step2_mine_following(context):
    """步骤2: 挖掘 Following 网络"""
    print("正在挖掘 Following 网络...")

    # 加载种子
    seeds_file = context["work_dir"] / "seeds.json"
    with open(seeds_file) as f:
        seeds = json.load(f)

    # 实际挖掘逻辑...
    # 这里支持断点续传
    results = []
    for seed in seeds:
        # 处理每个种子
        pass

    return {"new_candidates": len(results)}

def step3_quality_filter(context):
    """步骤3: 质量过滤"""
    print("正在进行质量过滤...")

    # 过滤逻辑
    return {"filtered": 100}

def step4_import_database(context):
    """步骤4: 导入数据库"""
    print("正在导入数据库...")

    # 导入逻辑
    return {"imported": 100}

def step5_generate_report(context):
    """步骤5: 生成报告"""
    print("正在生成报告...")

    # 报告逻辑
    return {"report": "report.pdf"}

def main():
    # 创建任务协调器
    coordinator = TaskCoordinator(
        task_name="github_mining_phase4",
        work_dir=Path("./tasks/github_mining")
    )

    # 定义任务流程
    coordinator.define_task("extract_seeds", step1_extract_seeds)
    coordinator.define_task("mine_following", step2_mine_following, dependencies=["extract_seeds"])
    coordinator.define_task("quality_filter", step3_quality_filter, dependencies=["mine_following"])
    coordinator.define_task("import_database", step4_import_database, dependencies=["quality_filter"])
    coordinator.define_task("generate_report", step5_generate_report, dependencies=["import_database"])

    # 执行任务（支持断点续传和自动重启）
    coordinator.run(auto_restart=True)

if __name__ == "__main__":
    AutoRestartWrapper.run(main, max_restarts=50)
```

---

### 示例 2: 启动和监控

```bash
# 1. 启动任务（后台运行）
nohup python3 tasks/github_mining_task.py > /dev/null 2>&1 &

# 2. 查看进度
./framework/monitor.sh github_mining_phase4

# 3. 查看实时日志
tail -f ./tasks/github_mining/github_mining_phase4.log

# 4. 手动恢复（如果进程被杀）
python3 tasks/github_mining_task.py  # 自动从断点继续

# 5. 查看状态文件
cat ./tasks/github_mining/github_mining_phase4_state.json
```

---

## 🎯 通用最佳实践

### 1. 任务设计原则

```python
# ✅ 好的任务设计
def good_task(context):
    # 幂等性：多次执行结果一致
    if output_file.exists():
        return {"status": "already_done"}

    # 原子性：要么全部成功，要么全部失败
    data = fetch_data()
    save_data(data)

    # 可观测：记录详细进度
    context["log"](f"已处理 {len(data)} 条记录")

    return {"processed": len(data)}

# ❌ 差的任务设计
def bad_task():
    # 非幂等：每次执行都会重复
    send_email()

    # 无原子性：中间状态无法恢复
    data1 = fetch1()
    data2 = fetch2()  # 如果这里失败，data1 已处理
    save(data1, data2)
```

### 2. 错误处理

```python
def robust_task(context):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            result = api_call()
            return result
        except RateLimitError as e:
            # API 限流：等待后重试
            wait_time = e.retry_after
            context["log"](f"API限流，等待 {wait_time} 秒")
            time.sleep(wait_time)
        except NetworkError:
            # 网络错误：指数退避
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

### 3. 进度保存

```python
def task_with_progress(context):
    # 初始化进度
    progress_file = context["work_dir"] / "task_progress.json"
    if progress_file.exists():
        progress = json.load(open(progress_file))
    else:
        progress = {"processed": 0, "total": 1000}

    # 批量处理
    batch_size = 100
    for i in range(progress["processed"], progress["total"], batch_size):
        batch = fetch_batch(i, batch_size)
        process_batch(batch)

        # 更新进度
        progress["processed"] = i + batch_size
        with open(progress_file, 'w') as f:
            json.dump(progress, f)

    return progress
```

---

## 📊 框架对比

| 特性 | 手动脚本 | 框架方案 |
|------|---------|---------|
| 断点续传 | ❌ 需手动实现 | ✅ 自动支持 |
| 自动重启 | ❌ 需人工介入 | ✅ 自动重启 |
| 进度追踪 | ❌ 难以查询 | ✅ JSON 文件 |
| 日志管理 | ❌ 分散在多处 | ✅ 统一日志 |
| 错误重试 | ❌ 需手动实现 | ✅ 自动重试 |
| 任务依赖 | ❌ 需手动管理 | ✅ 声明式管理 |

---

## 🎓 总结

### 核心要点

1. **状态持久化**: 所有进度保存到文件
2. **任务原子化**: 每个步骤可独立执行和恢复
3. **自动重启**: 失败后自动恢复执行
4. **进度可观测**: 随时查看任务状态

### 适用场景

- ✅ 长时间数据采集（爬虫、API 调用）
- ✅ 批量数据处理
- ✅ 机器学习模型训练
- ✅ 定时任务和 ETL 流程
- ✅ 任何需要 > 1 小时的任务

### 不适用场景

- ❌ 需要实时交互的任务
- ❌ 无法幂等重复执行的任务
- ❌ 状态必须保存在内存的任务

---

## 下一步

对于 GitHub Mining Phase 4 项目，我们可以：

1. 使用此框架重构任务流程
2. 每个步骤独立实现
3. 支持断点续传
4. 自动处理 API 限流
5. 实时进度监控

是否开始实施？
