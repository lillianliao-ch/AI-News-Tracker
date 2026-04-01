"""
OPC Event Bus — 跨系统事件通信的极简本地实现

设计原则（来自 OPC_strategy.md）：
- 从业务倒推基建。这个模块存在是因为 UCO 和 Headhunter 需要互通数据。
- 极简实现。用 SQLite 单表，不引入 Redis/RabbitMQ 等重型依赖。
- 生产者只管 emit，消费者按 event_type 订阅轮询。

使用方式：
  from opc_event_bus import EventBus
  bus = EventBus()
  bus.emit("NEW_AI_TRENDING_REPO", {"repo": "openai/gpt-5", "stars": 12000})
  events = bus.consume("NEW_AI_TRENDING_REPO", consumer_id="headhunter")
"""

import os
import json
import sqlite3
import time
from typing import List, Dict, Optional

# 事件总线数据库统一存放在全局位置
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "opc_event_bus.db"
)


class EventBus:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    source_system TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    consumed_by TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_consumed ON events(consumed_by)
            """)

    def emit(self, event_type: str, payload: dict, source_system: str = "unknown") -> int:
        """发射一个事件到总线。返回 event_id。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO events (event_type, source_system, payload) VALUES (?, ?, ?)",
                (event_type, source_system, json.dumps(payload, ensure_ascii=False))
            )
            return cursor.lastrowid

    def consume(self, event_type: str, consumer_id: str, limit: int = 50) -> List[Dict]:
        """
        消费指定类型的未处理事件。
        consumed_by 字段用逗号分隔记录已消费的 consumer，
        同一事件可以被多个 consumer 各消费一次。
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM events WHERE event_type = ? ORDER BY id ASC LIMIT ?",
                (event_type, limit * 3)  # 多取一些，后面过滤
            ).fetchall()

            results = []
            for row in rows:
                consumed_list = [c.strip() for c in row["consumed_by"].split(",") if c.strip()]
                if consumer_id not in consumed_list:
                    results.append({
                        "id": row["id"],
                        "event_type": row["event_type"],
                        "source_system": row["source_system"],
                        "payload": json.loads(row["payload"]),
                        "created_at": row["created_at"],
                    })
                    # 标记为已消费
                    consumed_list.append(consumer_id)
                    conn.execute(
                        "UPDATE events SET consumed_by = ? WHERE id = ?",
                        (",".join(consumed_list), row["id"])
                    )
                    if len(results) >= limit:
                        break

            return results

    def peek(self, event_type: str = None, limit: int = 10) -> List[Dict]:
        """查看最近的事件（不消费）。用于调试和监控。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if event_type:
                rows = conn.execute(
                    "SELECT * FROM events WHERE event_type = ? ORDER BY id DESC LIMIT ?",
                    (event_type, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(row) for row in rows]

    def stats(self) -> Dict:
        """返回总线统计信息。"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            types = conn.execute(
                "SELECT event_type, COUNT(*) as cnt FROM events GROUP BY event_type"
            ).fetchall()
            return {
                "total_events": total,
                "by_type": {row[0]: row[1] for row in types},
            }
