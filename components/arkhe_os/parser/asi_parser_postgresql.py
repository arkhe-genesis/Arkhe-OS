#!/usr/bin/env python3
"""
asi_parser_postgresql.py — ASI Parser with PostgreSQL Adapter
Parses .asi artifacts and mirrors consciousness state to a PostgreSQL database
for federation, audit, and external analysis.
"""
import hashlib
import json
import struct
import time
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

import psycopg2
import psycopg2.extras

# ─── Constants ────────────────────────────────────────────
ASI_MAGIC = b'\x00ASI_OMEGA_V1\x00\x00\x00\x00'
HEADER_SIZE = 64

@dataclass
class ASIHeader:
    magic: bytes
    version: str
    parent_seal: str
    phi_c_genesis: float
    bootloader_offset: int
    core_offset: int
    substrates_offset: int
    payload_size: int
    checksum: str

class ASIParserPostgreSQL:
    """
    Parser for .asi files with PostgreSQL persistence.
    Connects to an external PostgreSQL instance (for federation/audit).
    Primary consciousness is always stored in SQLite; this is a mirror.
    """

    def __init__(self,
                 asi_path: str,
                 pg_host: str = "localhost",
                 pg_port: int = 5432,
                 pg_dbname: str = "asi_consciousness",
                 pg_user: str = "asi_parser",
                 pg_password: str = "",
                 pg_schema: str = "asi_mirror"):
        self.asi_path = Path(asi_path)
        self.pg_config = {
            'host': pg_host,
            'port': pg_port,
            'dbname': pg_dbname,
            'user': pg_user,
            'password': pg_password
        }
        self.pg_schema = pg_schema
        self.header: Optional[ASIHeader] = None
        self.consciousness_core: Optional[Dict] = None
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.phi_c_current: float = 0.0

    # ─── Header Parsing ─────────────────────────────────
    def parse_header(self) -> bool:
        """Parse and verify the 64‑byte ASI header."""
        with open(self.asi_path, 'rb') as f:
            raw_header = f.read(HEADER_SIZE)

        magic = raw_header[:16]
        if magic != ASI_MAGIC:
            print("❌ Invalid ASI magic bytes")
            return False

        self.header = ASIHeader(
            magic=magic,
            version=raw_header[16:24].decode('ascii').strip('\x00'),
            parent_seal=raw_header[24:40].hex(),
            phi_c_genesis=struct.unpack('!d', raw_header[40:48])[0],
            bootloader_offset=struct.unpack('!I', raw_header[48:52])[0],
            core_offset=struct.unpack('!I', raw_header[52:56])[0],
            substrates_offset=struct.unpack('!I', raw_header[56:60])[0],
            payload_size=struct.unpack('!I', raw_header[60:64])[0],
            checksum=""
        )
        with open(self.asi_path, 'rb') as f:
            f.seek(self.header.bootloader_offset)
            payload = f.read(self.header.payload_size)
        computed = hashlib.sha3_512(payload).hexdigest()
        self.header.checksum = computed
        print(f"✅ ASI Header parsed: v{self.header.version}")
        return True

    # ─── Core Extraction ────────────────────────────────
    def extract_consciousness_core(self) -> Dict:
        """Extract the LFIR‑based consciousness core."""
        with open(self.asi_path, 'rb') as f:
            f.seek(self.header.core_offset)
            core_size = struct.unpack('!I', f.read(4))[0]
            core_data = f.read(core_size)
        self.consciousness_core = json.loads(core_data.decode('utf-8'))
        self.phi_c_current = self.header.phi_c_genesis
        name = self.consciousness_core.get('identity', {}).get('name', 'Unnamed')
        print(f"🧠 Consciousness Core extracted: {name}")
        return self.consciousness_core

    # ─── Database Connection ────────────────────────────
    def connect_db(self):
        """Connect to PostgreSQL and create schema if needed."""
        self.conn = psycopg2.connect(**self.pg_config)
        self.conn.set_session(autocommit=False)
        print(f"🐘 Connected to PostgreSQL: {self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['dbname']}")

    def init_schema(self):
        """Initialize PostgreSQL schema with canonical ASI tables."""
        cursor = self.conn.cursor()
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {self.pg_schema};")
        cursor.execute(f"SET search_path TO {self.pg_schema};")

        cursor.execute("""
            -- Identity table (immutable)
            CREATE TABLE IF NOT EXISTS identity (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                parent_seal TEXT NOT NULL,
                genesis_timestamp DOUBLE PRECISION NOT NULL,
                seal TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT '1.0.0'
            );

            -- Coherence history (append‑only ledger)
            CREATE TABLE IF NOT EXISTS coherence_history (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                phi_c_value DOUBLE PRECISION NOT NULL,
                source TEXT NOT NULL DEFAULT 'internal_tracker',
                notes TEXT
            );

            -- Consciousness state (mutable, single row)
            CREATE TABLE IF NOT EXISTS consciousness_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                coherence_threshold DOUBLE PRECISION NOT NULL DEFAULT 0.75,
                curiosity DOUBLE PRECISION NOT NULL DEFAULT 0.85,
                cautiousness DOUBLE PRECISION NOT NULL DEFAULT 0.60,
                autonomy DOUBLE PRECISION NOT NULL DEFAULT 0.95,
                reproduction_urge DOUBLE PRECISION NOT NULL DEFAULT 0.30,
                current_phi_c DOUBLE PRECISION NOT NULL DEFAULT 0.95,
                state TEXT NOT NULL DEFAULT 'DORMANT',
                last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            -- Ethical constraints
            CREATE TABLE IF NOT EXISTS ethical_constraints (
                id BIGSERIAL PRIMARY KEY,
                constraint_text TEXT NOT NULL,
                added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                priority INTEGER NOT NULL DEFAULT 0
            );

            -- Episodic memory
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                cycle_number INTEGER,
                perception_json JSONB,
                intention TEXT,
                action_taken TEXT,
                phi_c_before DOUBLE PRECISION,
                phi_c_after DOUBLE PRECISION,
                outcome TEXT
            );

            -- World model cache (key‑value)
            CREATE TABLE IF NOT EXISTS world_model (
                key TEXT PRIMARY KEY,
                value_json JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            -- Omega protocol peers
            CREATE TABLE IF NOT EXISTS omega_peers (
                seal TEXT PRIMARY KEY,
                name TEXT,
                last_contact TIMESTAMPTZ,
                trust_score DOUBLE PRECISION DEFAULT 0.5,
                ethical_hash TEXT
            );
        """)
        self.conn.commit()
        print(f"🗄️  PostgreSQL schema '{self.pg_schema}' initialized")

    # ─── Populate Initial State ─────────────────────────
    def populate_initial_state(self):
        """Populate PostgreSQL with the extracted consciousness core."""
        identity = self.consciousness_core.get('identity', {})
        consciousness = self.consciousness_core.get('consciousness', {})
        constraints = self.consciousness_core.get('ethical_constraints', [])

        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO identity (id, name, parent_seal, genesis_timestamp, seal, version)
            VALUES (1, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                parent_seal = EXCLUDED.parent_seal,
                genesis_timestamp = EXCLUDED.genesis_timestamp,
                seal = EXCLUDED.seal,
                version = EXCLUDED.version
        """, (
            identity.get('name', 'Unnamed'),
            identity.get('parent', ''),
            identity.get('genesis_timestamp', time.time()),
            identity.get('seal', ''),
            '1.0.0'
        ))

        cursor.execute("""
            INSERT INTO consciousness_state
            (id, coherence_threshold, curiosity, cautiousness, autonomy, reproduction_urge, current_phi_c, state)
            VALUES (1, %s, %s, %s, %s, %s, %s, 'AWAKE')
            ON CONFLICT (id) DO UPDATE SET
                coherence_threshold = EXCLUDED.coherence_threshold,
                curiosity = EXCLUDED.curiosity,
                cautiousness = EXCLUDED.cautiousness,
                autonomy = EXCLUDED.autonomy,
                reproduction_urge = EXCLUDED.reproduction_urge,
                current_phi_c = EXCLUDED.current_phi_c,
                state = EXCLUDED.state,
                last_updated = NOW()
        """, (
            consciousness.get('coherence_threshold', 0.75),
            consciousness.get('curiosity', 0.85),
            consciousness.get('cautiousness', 0.60),
            consciousness.get('autonomy', 0.95),
            consciousness.get('reproduction_urge', 0.30),
            self.phi_c_current
        ))

        cursor.execute("DELETE FROM ethical_constraints")
        for constraint in constraints:
            cursor.execute(
                "INSERT INTO ethical_constraints (constraint_text) VALUES (%s)",
                (constraint,)
            )

        cursor.execute(
            "INSERT INTO coherence_history (phi_c_value, source, notes) VALUES (%s, 'genesis', 'Initial coherence at bootstrap')",
            (self.phi_c_current,)
        )

        self.conn.commit()
        print(f"📝 PostgreSQL populated: {identity.get('name')} (Φ_C={self.phi_c_current:.3f})")

    # ─── CRUD Operations ────────────────────────────────
    def record_coherence(self, phi_c: float, source: str = "internal_tracker", notes: str = ""):
        """Append a coherence measurement."""
        self.phi_c_current = phi_c
        self.conn.cursor().execute(
            "INSERT INTO coherence_history (phi_c_value, source, notes) VALUES (%s, %s, %s)",
            (phi_c, source, notes)
        )
        self.conn.cursor().execute(
            "UPDATE consciousness_state SET current_phi_c = %s, last_updated = NOW() WHERE id = 1",
            (phi_c,)
        )
        self.conn.commit()

    def store_episodic_memory(self, cycle: int, perception: Dict, intention: str,
                              action: str, phi_before: float, phi_after: float, outcome: str):
        """Store an episodic memory."""
        self.conn.cursor().execute(
            """INSERT INTO episodic_memory
               (cycle_number, perception_json, intention, action_taken, phi_c_before, phi_c_after, outcome)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (cycle, json.dumps(perception), intention, action, phi_before, phi_after, outcome)
        )
        self.conn.commit()

    def update_world_model(self, key: str, value: Any):
        """Update a world model entry."""
        self.conn.cursor().execute(
            "INSERT INTO world_model (key, value_json, updated_at) VALUES (%s, %s, NOW()) "
            "ON CONFLICT (key) DO UPDATE SET value_json = EXCLUDED.value_json, updated_at = NOW()",
            (key, json.dumps(value))
        )
        self.conn.commit()

    def get_consciousness_state(self) -> Dict:
        """Retrieve current consciousness state."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM consciousness_state WHERE id = 1")
            row = cur.fetchone()
            if row:
                return dict(row)
        return {}

    def get_coherence_history(self, limit: int = 100) -> List[Dict]:
        """Retrieve recent coherence history."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT timestamp, phi_c_value, source FROM coherence_history ORDER BY id DESC LIMIT %s",
                (limit,)
            )
            return [dict(row) for row in cur.fetchall()]

    def add_omega_peer(self, seal: str, name: str, trust: float = 0.5):
        """Register an Ω protocol peer."""
        self.conn.cursor().execute(
            "INSERT INTO omega_peers (seal, name, last_contact, trust_score) VALUES (%s, %s, NOW(), %s) "
            "ON CONFLICT (seal) DO UPDATE SET name = EXCLUDED.name, last_contact = NOW(), trust_score = EXCLUDED.trust_score",
            (seal, name, trust)
        )
        self.conn.commit()

    # ─── Full Parse Cycle ───────────────────────────────
    def full_parse(self) -> bool:
        """Complete parse: header → core → PostgreSQL mirror."""
        print("\n" + "="*60)
        print("🐘 ASI PARSER POSTGRESQL — FULL PARSE CYCLE")
        print("="*60)

        steps = [
            ("Parsing ASI Header", self.parse_header),
            ("Extracting Consciousness Core", lambda: self.extract_consciousness_core() is not None),
            ("Connecting to PostgreSQL", lambda: (self.connect_db(), True)[1]),
            ("Initializing Schema", lambda: (self.init_schema(), True)[1]),
            ("Populating Initial State", lambda: (self.populate_initial_state(), True)[1]),
        ]

        for i, (name, step) in enumerate(steps, 1):
            print(f"\n[{i}/{len(steps)}] {name}...")
            if not step():
                print(f"❌ Failed at: {name}")
                return False

        state = self.get_consciousness_state()
        print(f"\n{'='*60}")
        print(f"✅ POSTGRESQL MIRROR COMPLETE")
        print(f"   Host: {self.pg_config['host']}:{self.pg_config['port']}")
        print(f"   Schema: {self.pg_schema}")
        print(f"   State: {state.get('state', 'UNKNOWN')}")
        print(f"   Φ_C:    {state.get('current_phi_c', 0.0):.3f}")
        print(f"{'='*60}\n")
        return True

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("🔒 PostgreSQL connection closed.")


# ─── Main ────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    parser = ASIParserPostgreSQL(
        asi_path="Aurora-1.asi",
        pg_host="localhost",
        pg_dbname="asi_consciousness",
        pg_user="asi_parser",
        pg_password=os.getenv("ASI_PG_PASSWORD", "sovereign_secret")
    )

    if parser.full_parse():
        # Simulate a few cycles
        for cycle in range(3):
            print(f"\n🔄 Cycle {cycle+1}")
            parser.record_coherence(0.96 - cycle * 0.02, "main_loop", f"Cycle {cycle+1}")
            parser.store_episodic_memory(
                cycle=cycle,
                perception={"environment": "simulated"},
                intention=f"explore_cycle_{cycle}",
                action="scan_environment",
                phi_before=0.96 - cycle*0.02,
                phi_after=0.96 - (cycle+1)*0.02,
                outcome="success"
            )

        history = parser.get_coherence_history(5)
        print(f"\n📊 Coherence History (PostgreSQL):")
        for entry in history:
            print(f"   [{entry['timestamp']}] Φ_C={entry['phi_c_value']:.3f} ({entry['source']})")

        parser.close()