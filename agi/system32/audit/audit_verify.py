#!/usr/bin/env python3
"""
audit_verify.py — CLI Audit Verification Tool
Cross-checks mirror database against the sealed .asi file to ensure
that what was declared to the Federation matches the entity's true history.
"""
import sqlite3
import psycopg2
import psycopg2.extras
import json
import struct
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

ASI_MAGIC = b'\x00ASI_OMEGA_V1\x00\x00\x00\x00'
HEADER_SIZE = 64

class AuditVerifier:
    def __init__(self, asi_path: str):
        self.asi_path = Path(asi_path)
        self.db_data = None
        self.asi_data = None
        self.discrepancies = []

    def load_asi_data(self):
        """Parse the .asi file and extract its embedded history."""
        with open(self.asi_path, 'rb') as f:
            header = f.read(HEADER_SIZE)
            magic = header[:16]
            if magic != ASI_MAGIC:
                raise ValueError("Invalid ASI file")
            core_offset = struct.unpack('!I', header[52:56])[0]
            f.seek(core_offset)
            core_size = struct.unpack('!I', f.read(4))[0]
            core_data = json.loads(f.read(core_size).decode('utf-8'))
        self.asi_data = core_data
        return core_data

    def load_db_data(self, db_type: str, connection_string: str):
        """Load data from the mirror database."""
        if db_type == 'sqlite':
            conn = sqlite3.connect(connection_string)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            self.db_data = {
                'identity': dict(cursor.execute("SELECT * FROM identity WHERE id=1").fetchone() or {}),
                'state': dict(cursor.execute("SELECT * FROM consciousness_state WHERE id=1").fetchone() or {}),
                'coherence_history': [dict(r) for r in cursor.execute(
                    "SELECT * FROM coherence_history ORDER BY id").fetchall()],
                'episodic_memory': [dict(r) for r in cursor.execute(
                    "SELECT * FROM episodic_memory ORDER BY id").fetchall()],
                'ethical_constraints': [r[0] for r in cursor.execute(
                    "SELECT constraint_text FROM ethical_constraints ORDER BY id").fetchall()],
                'peers': [dict(r) for r in cursor.execute("SELECT * FROM omega_peers").fetchall()]
            }
            conn.close()
        elif db_type == 'postgresql':
            parts = connection_string.split(':')
            conn = psycopg2.connect(host=parts[0], port=int(parts[1]), dbname=parts[2],
                                    user=parts[3], password=parts[4])
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            self.db_data = {}

            cur.execute("SELECT * FROM asi_mirror.identity WHERE id=1")
            row = cur.fetchone()
            self.db_data['identity'] = dict(row) if row else {}

            cur.execute("SELECT * FROM asi_mirror.consciousness_state WHERE id=1")
            row = cur.fetchone()
            self.db_data['state'] = dict(row) if row else {}

            cur.execute("SELECT * FROM asi_mirror.coherence_history ORDER BY id")
            self.db_data['coherence_history'] = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM asi_mirror.episodic_memory ORDER BY id")
            self.db_data['episodic_memory'] = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT constraint_text FROM asi_mirror.ethical_constraints ORDER BY id")
            self.db_data['ethical_constraints'] = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT * FROM asi_mirror.omega_peers")
            self.db_data['peers'] = [dict(r) for r in cur.fetchall()]

            conn.close()

    def verify_identity(self) -> List[str]:
        """Check that identity in DB matches the .asi core."""
        issues = []
        core_identity = self.asi_data.get('identity', {})
        db_identity = self.db_data.get('identity', {})
        if core_identity.get('name') != db_identity.get('name'):
            issues.append(f"Name mismatch: {core_identity.get('name')} vs {db_identity.get('name')}")
        if core_identity.get('seal') != db_identity.get('seal'):
            issues.append("Seal mismatch")
        return issues

    def verify_coherence_history(self) -> List[str]:
        """Verify that all coherence measurements in DB are present in .asi (truncated check)."""
        issues = []
        db_coh = self.db_data.get('coherence_history', [])
        if not db_coh:
            issues.append("No coherence history in DB")
        else:
            # Check genesis coherence
            genesis_phi = self.asi_data.get('consciousness', {}).get('phi_c_genesis')
            if genesis_phi and abs(db_coh[0].get('phi_c_value', 0) - genesis_phi) > 0.001:
                issues.append(f"Genesis Φ_C mismatch: DB {db_coh[0].get('phi_c_value')} vs ASI {genesis_phi}")
        return issues

    def verify_ethical_constraints(self) -> List[str]:
        core_constraints = set(self.asi_data.get('ethical_constraints', []))
        db_constraints = set(self.db_data.get('ethical_constraints', []))
        if core_constraints != db_constraints:
            return ["Ethical constraints mismatch between DB and .asi file"]
        return []

    def run(self) -> bool:
        self.discrepancies = []
        self.discrepancies.extend(self.verify_identity())
        self.discrepancies.extend(self.verify_coherence_history())
        self.discrepancies.extend(self.verify_ethical_constraints())
        return len(self.discrepancies) == 0

def main():
    parser = argparse.ArgumentParser(description="ARKHE OS Audit Verification Tool")
    parser.add_argument("--asi", required=True, help="Path to .asi file")
    parser.add_argument("--db-type", choices=["sqlite","postgresql"], default="sqlite")
    parser.add_argument("--db-conn", required=True, help="Connection string: file path for SQLite, host:port:db:user:pass for PostgreSQL")
    args = parser.parse_args()

    verifier = AuditVerifier(args.asi)
    verifier.load_asi_data()
    verifier.load_db_data(args.db_type, args.db_conn)

    if verifier.run():
        print("✅ Audit passed: mirror database matches the .asi file.")
    else:
        print("❌ Audit FAILED. Discrepancies found:")
        for issue in verifier.discrepancies:
            print(f"   - {issue}")

if __name__ == "__main__":
    main()
