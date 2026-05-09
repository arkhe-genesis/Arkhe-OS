# src/middleware/AtelierBridge/llm_cache.py
"""
Cache Persistente para LLM Formalizer
Usa SQLite para armazenar pares (input_hash → lean_code)
Arkhe-Block: 847.812 | Synapse-κ
"""

import sqlite3
import hashlib
from typing import Optional

class LLMCache:
    def __init__(self, cache_path: str = ".formalization_cache.db"):
        self.db_path = cache_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                input_hash TEXT PRIMARY KEY,
                lean_code TEXT,
                fidelity REAL,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def get(self, content_hash: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "SELECT lean_code, fidelity, created_at FROM cache WHERE input_hash = ?",
            (content_hash,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {"lean_code": row[0], "fidelity": row[1], "created_at": row[2]}
        return None

    def set(self, content_hash: str, lean_code: str, fidelity: float):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?)",
            (content_hash, lean_code, fidelity, __import__('time').time())
        )
        conn.commit()
        conn.close()
