# GitHub Mining: 下一步架构优化方案 (MVP 进阶版)

基于《GitHub Mining 项目架构分析与设计评审》以及我们当前的业务重点（**敏捷跑批、重构债务、稳定交付**），我为你制定了这份切实可行的优化方案。

这份方案**摒弃了那些为了“大厂架构而架构”的过度设计**（如微服务、Kafka流处理），专注于解决当前**脚本化工程**最痛的几个点，让系统具备稳定跑几十万量级数据的能力。

---

## 🚀 第一阶段：核心防御与解耦 (预计 1-2 周)
*目标：让现在的单体脚本系统坚不可摧，彻底告别“因为一个网络异常整个批次白跑”的窘境。*

### 1. 全局配置收拢 (Configuration Strategy)
当前配置散落在 `github_hunter_config.py` 和各个脚本的开头（如 API Key 读取）。
- **行动**：建立单一的 `config.yaml` 或正式的 `.env` 方案。
- **价值**：避免测试环境和生产环境 Token 混用，防止密钥泄露至代码仓库。
- **验收标准**：
  - ✅ 所有 Token 从 `config.yaml`读取
  - ✅ 无硬编码的 API Key
  - ✅ 支持 dev/prod 环境切换

### 2. 构建核心网络中间件 (API Resiliency)
目前的 GitHub API 和 DashScope (LLM) 调用散乱，且对 HTTP Error (如 403, 429) 抵抗力弱。
- **行动**：提取一个通用的 `api_client.py`。
- **技术点**：
  - 封装 Requests Session (连接池)，极大提升并发请求速度。
  - 使用 `@retry` 装饰器统一处理限流（如 `urllib3.util.retry.Retry` 的指数退避策略）。
- **价值**：在跑大批次（如 10,000+）时，不会因为某几秒的 GitHub 抽风导致进程异常终止。
- **验收标准**：
  - ✅ 429 错误自动重试 3 次
  - ✅ 连接池提升并发 50%+
  - ✅ 所有 API 调用统一走 `api_client`

### 3. 公共基础组件下沉 (Commons Extraction)
- **行动**：剥离 `github_network_miner.py` 中的大量非核心业务代码。
- **拆分目标**：
  - `data_io.py`: 专门负责读写 JSON（支持海量数据流式处理如 `ijson`）。
  - `logger.py`: 统一格式化输出带时间戳、级别的前缀日志，取代当前遍地开花的 `print()` / `log()` 混用。
- **验收标准**：
  - ✅ 所有 `print()` 替换为 `logger`
  - ✅ 所有 JSON 读写走 `data_io`
  - ✅ 代码行数减少 30%+

---

## ⚙️ 第二阶段：质量控制与敏捷化 (预计 1 个月)
*目标：降低人工检查成本，保证丢进去的数据和跑出来的数据 100% 结构对齐。*

### 1. 业务逻辑自动化验证 (Data Quality Assertions)
当前强依赖人工跑脚本或者肉眼看命令行梳理。
- **行动**：引入结构化数据断言类（类似于小型的 Pydantic Schemas）。
- **具体实施**：
  - 拦截可能污染数据库的脏数据。
- **具体规则与实现示例 (P1 优先级)**：
  建议将验证逻辑下沉至专用的 `lib/data_quality.py` 模块：

  ```python
  from typing import List, Dict
  from dataclasses import dataclass

  @dataclass
  class QualityRule:
      name: str
      check: callable
      threshold: float
      error_message: str

  class PhaseValidator:
      def __init__(self, phase: str):
          self.phase = phase
          self.rules = self._load_rules()

      def validate(self, data: List[Dict]) -> List[str]:
          violations = []
          for rule in self.rules:
              if not rule.check(data):
                  violations.append(rule.error_message)
          return violations

  # 具体规则示例 (Phase 3)
  PHASE3_RULES = [
      QualityRule(
          name="email_coverage",
          check=lambda data: sum(1 for u in data if u.get('email')) / len(data) >= 0.5,
          threshold=0.5,
          error_message="邮箱覆盖率低于 50%"
      ),
      QualityRule(
          name="no_org_accounts",
          check=lambda data: all(u.get('type') != 'Organization' for u in data),
          threshold=1.0,
          error_message="检测到组织账号混入"
      ),
  ]

  # 在写入 JSON 前拦截
  validator = PhaseValidator("phase3")
  violations = validator.validate(phase3_output)
  if violations:
      logger.error(f"Phase 3 质量检查失败: {violations}")
      raise DataQualityError(violations)
  ```

### 2. 核心过滤逻辑的单元测试 (Unit Testing the Filters)
- **行动**：对判定核心（如判别是否为 AI 人才、判别组织账号等）引入 `pytest`。
- **价值**：以后无论 prompt 怎么升级、或 GitHub 数据结构怎么变，只要跑一遍测试用例就能保证“核心漏斗”没被破坏。这是唯一能在业务敏捷变动中给你安全感的东西。

### 3. 断点管理的小型性能优化 (O(1) 查找)
现有的断点续传是基于记事本增量写入（`{"completed": []}`）。目前代码中可能存在 O(n) 的列表遍历。
- **现状与痛点**：当人数膨胀到 10 万级，如果在 `list` 中查找 `if username in completed_list` 会随着进度越来越慢。
- **行动 (避免过度设计)**：不需要引入 SQLite 或外部数据库。只需在内存中将判断用的列表转化为集合。
- **具体实施**：
  ```python
  # 简单优化：使用集合而不是列表
  # ❌ 慢（O(n)）
  # if username in completed_list: continue

  # ✅ 快（O(1)）
  completed_set = set(completed_list)
  if username in completed_set:
      continue
  ```
- **阀门约定**：只有当单批次数据量 > 50万，遇到严重内存/序列化瓶颈时，才考虑架构跃迁（如 SQLite）。

---

## 🛑 第三阶段：坚决【不要】做的事情 (反向建议)

为了保证团队精力聚焦在“为猎头库带来高质量人才”这个核心 KPI 上，以下架构师报告里的建议，在系统稳定日均产出不满万级之前，**强烈建议不碰**：

1. **❌ 微服务化 (FastAPI + Celery + Docker)**：
   运维成本太高，目前不需要复杂的任务分发网。单机的 Python `nohup` 配合我们的隔离批次文件（`runs/`）已经足够强壮。
2. **❌ 实时数据流 (Kafka + Flink)**：
   本业务属于“T+1”或“每周定时”的**离线批处理 (Batch)** 场景，搞流式事件驱动毫无业务收益。
3. **❌ 知识图谱数据库 (Neo4j)**：
   虽然听起来高大上，但在现有的关系型库 (SQLite/PostgreSQL) 里用 JSON 字段配合向量检索（如果有）已经完全能解决 95% 的人员匹配问题了。

---
**Summary**: 我们接下来的优化动作，就应该围绕着 **“如何把这个 Python 脚本群，打造成一把锋利、硬核且绝不生锈的瑞士军刀”** 来做，而不是去建造一个航空母舰。

你觉得我们可以在正式跑起一万人的批次之后，优先从**第一阶段（解耦与重试防御机制）**开始动手吗？
