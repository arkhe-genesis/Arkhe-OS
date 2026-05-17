# src/arkhe/layers/engineering/schema_migration.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import hashlib, time, json

@dataclass
class SchemaVersion:
    version: int
    migration_sql: str
    rollback_sql: str
    dependencies: List[int] = field(default_factory=list)
    checksum: str = ""

    def compute_checksum(self):
        self.checksum = hashlib.sha3_256(
            f"{self.version}:{self.migration_sql}:{self.rollback_sql}".encode()
        ).hexdigest()[:16]

class SchemaMigrationOrchestrator:
    def __init__(self, current_version: int, ledger):
        self.current = current_version
        self.ledger = ledger
        self.history = []

    def plan_migration(self, target: int, migrations: Dict[int, SchemaVersion]):
        path = []
        while target > self.current:
            step = self.current + 1
            if step not in migrations:
                raise ValueError(f"No migration for version {step}")
            path.append(migrations[step])
            self.current = step
        return path

    def migrate(self, db, target: int, dry_run=True):
        path = self.plan_migration(target, self.load_migrations())
        for m in path:
            # dual-write: apply to shadow db first
            shadow = db.clone()
            try:
                shadow.execute(m.migration_sql)
                # verify checksum of shadow state
                new_checksum = hashlib.sha3_256(
                    json.dumps(shadow.schema_hash()).encode()
                ).hexdigest()[:16]
                m.compute_checksum()
                if new_checksum != m.checksum:
                    raise RuntimeError("Shadow migration checksum mismatch")
                if not dry_run:
                    db.execute(m.migration_sql)
                self.history.append({'version': m.version, 'timestamp': time.time_ns()})
            except Exception as e:
                # rollback shadow and stop
                shadow.execute(m.rollback_sql)
                raise e
        # anchor successful migration in temporal ledger
        self.ledger.record('schema_migration', {'from': self.current - len(path), 'to': target})
        return True
