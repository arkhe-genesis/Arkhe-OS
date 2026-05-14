#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sqlite.py — Backend SQLite para TemporalChain.
Ideal para desenvolvimento e ambientes de pequena escala.
"""

import sqlite3
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base import StorageBackend
from ..core import Anchor, Event, EventType, CausalLink

class SQLiteStorage(StorageBackend):
    """Backend SQLite com suporte a consultas eficientes."""

    def __init__(self, config: Dict):
        self.db_path = Path(config.get("path", "timechain.db")).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self):
        """Inicializa schema do banco de dados."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabela de âncoras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anchors (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                metadata TEXT NOT NULL,
                timestamp REAL NOT NULL,
                seal TEXT NOT NULL UNIQUE,
                previous_seal TEXT NOT NULL,
                chain_seal TEXT NOT NULL,
                position INTEGER NOT NULL,
                anchored_at REAL NOT NULL,
                causal_deps TEXT
            )
        """)

        # Índices para consultas frequentes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON anchors(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON anchors(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_seal ON anchors(seal)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_position ON anchors(position)")

        # Tabela de estado da cadeia
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chain_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    async def save_anchor(self, anchor: Anchor) -> bool:
        """Salva âncora no SQLite."""
        def _save():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO anchors
                (event_id, event_type, payload, metadata, timestamp, seal,
                 previous_seal, chain_seal, position, anchored_at, causal_deps)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                anchor.event.event_id,
                anchor.event.event_type.value,
                json.dumps(anchor.event.payload),
                json.dumps(anchor.event.metadata),
                anchor.event.timestamp,
                anchor.event.seal,
                anchor.previous_seal,
                anchor.chain_seal,
                anchor.position,
                anchor.anchored_at,
                json.dumps([d.to_dict() for d in anchor.event.causal_deps]),
            ))

            conn.commit()
            conn.close()
            return True

        return await asyncio.to_thread(_save)

    async def get_anchor_by_event_id(self, event_id: str) -> Optional[Anchor]:
        """Recupera âncora por event_id."""
        def _query():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM anchors WHERE event_id = ?", (event_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_anchor(row)
            return None

        return await asyncio.to_thread(_query)

    async def get_anchor_by_seal(self, seal: str) -> Optional[Anchor]:
        """Recupera âncora por selo."""
        def _query():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM anchors WHERE seal = ?", (seal,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_anchor(row)
            return None

        return await asyncio.to_thread(_query)

    async def query_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        seal_prefix: Optional[str] = None,
        causal_filter: Optional[Dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """Consulta eventos com filtros."""
        def _query():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM anchors WHERE 1=1"
            params = []

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            if seal_prefix:
                query += " AND seal LIKE ?"
                params.append(f"{seal_prefix}%")

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_anchor(row).event for row in rows]

        return await asyncio.to_thread(_query)

    async def get_anchors_range(self, start: int, end: int) -> List[Anchor]:
        """Recupera âncoras em um intervalo de posições."""
        def _query():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM anchors WHERE position >= ? AND position < ? ORDER BY position ASC", (start, end))
            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_anchor(row) for row in rows]

        return await asyncio.to_thread(_query)

    async def save_chain_state(self, state: Dict[str, Any]) -> bool:
        """Salva estado da cadeia (seal atual, count, merkle root)."""
        def _save():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("INSERT OR REPLACE INTO chain_state (key, value) VALUES (?, ?)", ("state", json.dumps(state)))

            conn.commit()
            conn.close()
            return True

        return await asyncio.to_thread(_save)

    def load_chain_state(self) -> Optional[Dict[str, Any]]:
        """Carrega estado da cadeia do storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chain_state'")
        if not cursor.fetchone():
            conn.close()
            return None

        cursor.execute("SELECT value FROM chain_state WHERE key = ?", ("state",))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def _row_to_anchor(self, row: tuple) -> Anchor:
        """Converte linha do banco para objeto Anchor."""
        event = Event(
            event_id=row[0],
            event_type=EventType(row[1]),
            payload=json.loads(row[2]),
            metadata=json.loads(row[3]),
            timestamp=row[4],
            seal=row[5],
            causal_deps=[CausalLink.from_dict(d) for d in json.loads(row[10] or "[]")],
        )
        return Anchor(
            event=event,
            previous_seal=row[6],
            chain_seal=row[7],
            position=row[8],
            anchored_at=row[9],
        )

    @property
    def supports_replication(self) -> bool:
        return False  # SQLite é local
