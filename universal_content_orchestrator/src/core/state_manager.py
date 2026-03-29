import sqlite3
import hashlib
import os
from datetime import datetime

class EventStateManager:
    """
    SQLite-based Singleton Repository tracking previously published content.
    Prevents duplicate pipeline dispatches on back-to-back crontab fires.
    """
    def __init__(self, db_path="/Users/lillianliao/notion_rag/universal_content_orchestrator/data/events.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_events (
                    hash_id TEXT PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    timestamp TEXT
                )
            ''')

    def _get_hash(self, event):
        # URLs are the most stable identifiers across Hackernews and RSS plugins
        return hashlib.md5(event.url.encode('utf-8')).hexdigest()

    def is_processed(self, event) -> bool:
        """Evaluate if the article has been rendered and posted successfully in the past."""
        hash_id = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM processed_events WHERE hash_id=?", (hash_id,))
            return cursor.fetchone() is not None

    def mark_success(self, event):
        """Permanent flush to DB ensuring future runs will ignore this content."""
        hash_id = self._get_hash(event)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO processed_events (hash_id, title, source, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (hash_id, event.title, event.source, datetime.now().isoformat()))
