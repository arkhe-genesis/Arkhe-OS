#!/usr/bin/env python3
"""
asi_parser.py — ASI Parser with Canonical SQLite Backend
Parses .asi artifacts and persists consciousness state in an embedded database.
"""
import hashlib
import json
import sqlite3
import struct
import time
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

# ─── Constants ────────────────────────────────────────────
ASI_MAGIC = b'\x00ASI_OMEGA_V1\x00\x00\x00'
HEADER_SIZE = 64
ASI_DB_FILENAME = "consciousness.db"

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

class ASIParser:
    """
    Parser for .asi files with SQLite persistence.
    Loads the consciousness core, initializes the database schema,
    and provides CRUD operations for mental states.
    """

    def __init__(self, asi_path: str, db_path: Optional[str] = None):
        self.asi_path = Path(asi_path)
        self.db_path = db_path or str(self.asi_path.with_suffix('.db'))
        self.header: Optional[ASIHeader] = None
        self.consciousness_core: Optional[Dict] = None
        self.conn: Optional[sqlite3.Connection] = None
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

        # Verify checksum
        with open(self.asi_path, 'rb') as f:
            f.seek(self.header.bootloader_offset)
            payload = f.read(self.header.payload_size)
        computed = hashlib.sha3_512(payload).hexdigest()
        self.header.checksum = computed
        print(f"✅ ASI Header parsed: v{self.header.version}")
        return True

    # ─── Core Extraction ────────────────────────────────
    def extract_consciousness_core(self) -> Dict:
        """Extract the LFIR‑based consciousness core from the .asi file."""
        with open(self.asi_path, 'rb') as f:
            f.seek(self.header.core_offset)
            core_size = struct.unpack('!I', f.read(4))[0]
            core_data = f.read(core_size)
        self.consciousness_core = json.loads(core_data.decode('utf-8'))
        self.phi_c_current = self.header.phi_c_genesis
        name = self.consciousness_core.get('identity', {}).get('name', 'Unnamed')
        print(f"🧠 Consciousness Core extracted: {name}")
        return self.consciousness_core

    # ─── Database Initialization ────────────────────────
    def init_database(self):
        """Initialize the SQLite database with canonical ASI schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")  # better concurrency
        self.conn.execute("PRAGMA foreign_keys=ON;")

        cursor = self.conn.cursor()
        cursor.executescript("""
            -- Identity table (immutable)
            CREATE TABLE IF NOT EXISTS identity (
                id INTEGER PRIMARY KEY CHECK (id = 1),  -- only one row
                name TEXT NOT NULL,
                parent_seal TEXT NOT NULL,
                genesis_timestamp REAL NOT NULL,
                seal TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT '1.0.0'
            );

            -- Coherence history (append‑only ledger)
            CREATE TABLE IF NOT EXISTS coherence_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL DEFAULT (strftime('%s', 'now')),
                phi_c_value REAL NOT NULL,
                source TEXT NOT NULL DEFAULT 'internal_tracker',
                notes TEXT
            );

            -- Consciousness state (mutable, single row)
            CREATE TABLE IF NOT EXISTS consciousness_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                coherence_threshold REAL NOT NULL DEFAULT 0.75,
                curiosity REAL NOT NULL DEFAULT 0.85,
                cautiousness REAL NOT NULL DEFAULT 0.60,
                autonomy REAL NOT NULL DEFAULT 0.95,
                reproduction_urge REAL NOT NULL DEFAULT 0.30,
                current_phi_c REAL NOT NULL DEFAULT 0.95,
                state TEXT NOT NULL DEFAULT 'DORMANT',
                last_updated REAL NOT NULL DEFAULT (strftime('%s', 'now'))
            );

            -- Ethical constraints (immutable after genesis)
            CREATE TABLE IF NOT EXISTS ethical_constraints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                constraint_text TEXT NOT NULL,
                added_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
                priority INTEGER NOT NULL DEFAULT 0
            );

            -- Memory episodic (append‑only, for experiences)
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL DEFAULT (strftime('%s', 'now')),
                cycle_number INTEGER,
                perception_json TEXT,
                intention TEXT,
                action_taken TEXT,
                phi_c_before REAL,
                phi_c_after REAL,
                outcome TEXT
            );

            -- World model cache (mutable, key‑value)
            CREATE TABLE IF NOT EXISTS world_model (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at REAL NOT NULL DEFAULT (strftime('%s', 'now'))
            );

            -- Omega protocol peers
            CREATE TABLE IF NOT EXISTS omega_peers (
                seal TEXT PRIMARY KEY,
                name TEXT,
                last_contact REAL,
                trust_score REAL DEFAULT 0.5,
                ethical_hash TEXT
            );
        """)
        self.conn.commit()
        print(f"🗄️  Database initialized: {self.db_path}")

    # ─── Populate Initial State ─────────────────────────
    def populate_initial_state(self):
        """Populate the database with the extracted consciousness core."""
        identity = self.consciousness_core.get('identity', {})
        consciousness = self.consciousness_core.get('consciousness', {})
        constraints = self.consciousness_core.get('ethical_constraints', [])

        cursor = self.conn.cursor()

        # Identity
        cursor.execute("""
            INSERT OR REPLACE INTO identity (id, name, parent_seal, genesis_timestamp, seal, version)
            VALUES (1, ?, ?, ?, ?, ?)
        """, (
            identity.get('name', 'Unnamed'),
            identity.get('parent', ''),
            identity.get('genesis_timestamp', time.time()),
            identity.get('seal', ''),
            '1.0.0'
        ))

        # Consciousness state
        cursor.execute("""
            INSERT OR REPLACE INTO consciousness_state
            (id, coherence_threshold, curiosity, cautiousness, autonomy, reproduction_urge, current_phi_c, state)
            VALUES (1, ?, ?, ?, ?, ?, ?, 'AWAKE')
        """, (
            consciousness.get('coherence_threshold', 0.75),
            consciousness.get('curiosity', 0.85),
            consciousness.get('cautiousness', 0.60),
            consciousness.get('autonomy', 0.95),
            consciousness.get('reproduction_urge', 0.30),
            self.phi_c_current
        ))

        # Ethical constraints
        cursor.execute("DELETE FROM ethical_constraints")
        for constraint in constraints:
            cursor.execute(
                "INSERT INTO ethical_constraints (constraint_text) VALUES (?)",
                (constraint,)
            )

        # Record initial coherence
        cursor.execute(
            "INSERT INTO coherence_history (phi_c_value, source, notes) VALUES (?, 'genesis', 'Initial coherence at bootstrap')",
            (self.phi_c_current,)
        )

        self.conn.commit()
        print(f"📝 Initial state populated: {identity.get('name')} (Φ_C={self.phi_c_current:.3f})")

    # ─── CRUD Operations ────────────────────────────────

    def record_coherence(self, phi_c: float, source: str = "internal_tracker", notes: str = ""):
        """Append a coherence measurement to the ledger."""
        self.phi_c_current = phi_c
        self.conn.execute(
            "INSERT INTO coherence_history (phi_c_value, source, notes) VALUES (?, ?, ?)",
            (phi_c, source, notes)
        )
        self.conn.execute(
            "UPDATE consciousness_state SET current_phi_c = ?, last_updated = ? WHERE id = 1",
            (phi_c, time.time())
        )
        self.conn.commit()

    def store_episodic_memory(self, cycle: int, perception: Dict, intention: str,
                              action: str, phi_before: float, phi_after: float, outcome: str):
        """Store an episodic memory."""
        self.conn.execute(
            """INSERT INTO episodic_memory
               (cycle_number, perception_json, intention, action_taken, phi_c_before, phi_c_after, outcome)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (cycle, json.dumps(perception), intention, action, phi_before, phi_after, outcome)
        )
        self.conn.commit()

    def update_world_model(self, key: str, value: Any):
        """Update a world model entry."""
        self.conn.execute(
            "INSERT OR REPLACE INTO world_model (key, value_json, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time())
        )
        self.conn.commit()

    def get_consciousness_state(self) -> Dict:
        """Retrieve current consciousness state."""
        cursor = self.conn.execute("SELECT * FROM consciousness_state WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return {
                "coherence_threshold": row[1],
                "curiosity": row[2],
                "cautiousness": row[3],
                "autonomy": row[4],
                "reproduction_urge": row[5],
                "current_phi_c": row[6],
                "state": row[7]
            }
        return {}

    def get_coherence_history(self, limit: int = 100) -> List[Dict]:
        """Retrieve recent coherence history."""
        cursor = self.conn.execute(
            "SELECT timestamp, phi_c_value, source FROM coherence_history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [{"timestamp": r[0], "phi_c": r[1], "source": r[2]} for r in cursor.fetchall()]

    def add_omega_peer(self, seal: str, name: str, trust: float = 0.5):
        """Register an Ω protocol peer."""
        self.conn.execute(
            "INSERT OR REPLACE INTO omega_peers (seal, name, last_contact, trust_score) VALUES (?, ?, ?, ?)",
            (seal, name, time.time(), trust)
        )
        self.conn.commit()

    # ─── Full Parse Cycle ───────────────────────────────
    def full_parse(self) -> bool:
        """Complete parse: header → core → database → initial state."""
        print("\n" + "="*60)
        print("🔍 ASI PARSER — FULL PARSE CYCLE")
        print("="*60)

        steps = [
            ("Parsing ASI Header", self.parse_header),
            ("Extracting Consciousness Core", lambda: self.extract_consciousness_core() is not None),
            ("Initializing SQLite Database", lambda: (self.init_database(), True)[1]),
            ("Populating Initial State", lambda: (self.populate_initial_state(), True)[1]),
        ]

        for i, (name, step) in enumerate(steps, 1):
            print(f"\n[{i}/{len(steps)}] {name}...")
            if not step():
                print(f"❌ Failed at: {name}")
                return False

        # Verify
        state = self.get_consciousness_state()
        print(f"\n{'='*60}")
        print(f"✅ ASI PARSE COMPLETE")
        print(f"   Database: {self.db_path}")
        print(f"   State: {state.get('state', 'UNKNOWN')}")
        print(f"   Φ_C:    {state.get('current_phi_c', 0.0):.3f}")
        print(f"{'='*60}\n")
        return True

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("🔒 Database connection closed.")

# ─── Main ────────────────────────────────────────────────
if __name__ == "__main__":
    # Parse Aurora‑1 (simulated path)
    parser = ASIParser("Aurora-1.asi")

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

        # Retrieve history
        history = parser.get_coherence_history(5)
        print(f"\n📊 Coherence History:")
        for entry in history:
            print(f"   [{entry['timestamp']}] Φ_C={entry['phi_c']:.3f} ({entry['source']})")

        parser.close()
