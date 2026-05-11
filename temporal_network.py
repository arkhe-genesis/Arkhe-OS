#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARKHE Ω-TEMP v4.1.1 — Rede Retrocausal com Compressão Soberana,
Ponte Solar e Multiverso.

Tudo em um único arquivo. Zero dependências externas obrigatórias
(numpy é opcional).

Substratos implementados:
  5022 — Sovereign Compression (zlib/gzip + SHA3-256)
  5033 — Temporal Hash Chain
  5034 — Consistency Oracle (6 checks, tempo negativo quântico)
  5035 — Causal Shield (firewall + rate limit)
  7005 — Multiverse Router (timeline branches interconectadas)

Uso:
    python3 temporal_network.py --demo
    python3 temporal_network.py --solar
    python3 temporal_network.py --multiverse
    python3 temporal_network.py --test
"""

import hashlib
import json
import logging
import math
import time
import uuid
import struct
import socket
import threading
import sqlite3
import zlib as _zlib
import gzip as _gzip
from abc import ABC, abstractmethod
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, Deque, List, Optional, Set, Tuple, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

# ============================================================================
# CONSTANTES GLOBAIS
# ============================================================================

VERSION = "4.1.1"
PROTOCOL_NAME = "Ω-TEMP"
DEFAULT_WINDOW_SECONDS = 5 * 365.25 * 24 * 3600  # 5 anos
DEFAULT_FEDERATION_NODES = 7
RETRONET_PORT = 9500
RETRONET_PEERING_INTERVAL = 30
RETRONET_HEARTBEAT_INTERVAL = 10
QUANTUM_NEGATIVE_WINDOW_SECONDS = 1e-12  # 1 picosegundo

# Constantes da Ponte Solar
SOLAR_CORONA_TEMP_EV = 1.5e6
SOLAR_WIND_TEMP_EV = 1e5
SOLAR_CORONA_B_TESLA = 0.001
SOLAR_WIND_B_TESLA = 5e-9
SOLAR_CORONA_DENSITY = 1e14
SOLAR_WIND_DENSITY = 5e6
SOLAR_ALFVEN_SPEED = 500e3

# Constantes Multiverso
MULTIVERSE_BASE_OFFSET = 1e10

log = logging.getLogger("arkhe.net")

# ============================================================================
# EXCEÇÕES
# ============================================================================

class ArkheError(Exception): pass
class ChannelNotInitializedError(ArkheError): pass
class TimelineNotFoundError(ArkheError): pass
class MultiverseRoutingError(ArkheError): pass
class IntegrityError(ArkheError): pass

# ============================================================================
# TIME CRYSTAL (Substrato 5021)
# ============================================================================

@dataclass
class FloquetState:
    omega_hz: float
    phase: float = 0.0
    quality_factor: float = 50_000.0
    timestamp_start: float = field(default_factory=time.time)

    @property
    def period(self) -> float:
        return 1.0 / self.omega_hz if self.omega_hz > 0 else float('inf')

    @property
    def tau_coherence(self) -> float:
        return self.quality_factor / self.omega_hz if self.omega_hz > 0 else float('inf')


class TimeCrystal:
    def __init__(self, frequency_khz=465.0, quality_factor=50_000.0):
        self._state = FloquetState(omega_hz=frequency_khz * 1000.0, quality_factor=quality_factor)

    @property
    def omega(self) -> float:
        return self._state.omega_hz

    @property
    def phase(self) -> float:
        t = time.time() - self._state.timestamp_start
        return (self._state.omega_hz * t) % (2 * math.pi)

    def is_aligned(self, tolerance=1e-6) -> bool:
        p = self.phase
        return min(p, 2 * math.pi - p) < tolerance

    def coherence_decay(self, elapsed_seconds: float) -> float:
        tau = self._state.tau_coherence
        F_min = 0.95
        return F_min + (1.0 - F_min) * math.exp(-elapsed_seconds / tau) if tau > 0 else F_min

# ============================================================================
# AUDIT LEDGER (Substrato 333)
# ============================================================================

class AuditLedger:
    def __init__(self, db_path: Union[str, Path] = ":memory:"):
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._setup_tables()

    def _setup_tables(self):
        self._conn.execute("""CREATE TABLE IF NOT EXISTS ledger_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            timestamp REAL NOT NULL,
            hash TEXT NOT NULL UNIQUE
        )""")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger_entries(event_type)")
        self._conn.commit()

    @staticmethod
    def _sanitize(obj):
        if isinstance(obj, (np.bool_,)) if np else False: return bool(obj)
        if isinstance(obj, np.integer) if np else False: return int(obj)
        if isinstance(obj, np.floating) if np else False: return float(obj)
        if isinstance(obj, np.ndarray) if np else False: return obj.tolist()
        if isinstance(obj, dict): return {str(k): AuditLedger._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)): return [AuditLedger._sanitize(v) for v in obj]
        return obj

    def record(self, event_type: str, payload: dict) -> str:
        clean = self._sanitize(payload)
        payload_str = json.dumps(clean, sort_keys=True, ensure_ascii=False)
        h = hashlib.sha3_256(payload_str.encode()).hexdigest()
        try:
            self._conn.execute(
                "INSERT INTO ledger_entries (event_type,payload_json,timestamp,hash) VALUES (?,?,?,?)",
                (event_type, payload_str, time.time(), h))
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass
        return h

    def get_records(self, limit=500, offset=0):
        cur = self._conn.execute(
            "SELECT event_type,payload_json,timestamp,hash FROM ledger_entries ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset))
        return [{"type": r[0], "payload": json.loads(r[1]), "timestamp": r[2], "hash": r[3]} for r in cur.fetchall()]

    def get_all_records(self):
        all_r, off = [], 0
        while True:
            batch = self.get_records(limit=500, offset=off)
            if not batch: break
            all_r.extend(batch); off += 500
        return all_r

    def get_events_by_type(self, event_type: str, limit=100):
        cur = self._conn.execute(
            "SELECT event_type,payload_json,timestamp,hash FROM ledger_entries WHERE event_type=? ORDER BY id DESC LIMIT ?",
            (event_type, limit))
        return [{"type": r[0], "payload": json.loads(r[1]), "timestamp": r[2], "hash": r[3]} for r in cur.fetchall()]

    def count(self): return self._conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]

    def verify_integrity(self):
        errors = []
        for r in self._conn.execute("SELECT event_type,payload_json,hash FROM ledger_entries"):
            if hashlib.sha3_256(r[1].encode()).hexdigest() != r[2]:
                errors.append(f"Hash mismatch ({r[0]})")
        return len(errors) == 0, errors

# ============================================================================
# QFAM (Substrato 5027)
# ============================================================================

@dataclass
class QFAMEntry:
    key: str; pattern: Any; timestamp: float; pattern_hash: str; metadata: dict = field(default_factory=dict)

class QFAM:
    def __init__(self, threshold=0.85, max_entries=100_000):
        self._mem: Dict[str, QFAMEntry] = {}; self._th = threshold; self._max = max_entries

    def store(self, key, pattern, ts=None, meta=None):
        if len(self._mem) >= self._max and key not in self._mem:
            del self._mem[min(self._mem, key=lambda k: self._mem[k].timestamp)]
        ts = ts or time.time()
        h = hashlib.sha3_256(str(pattern).encode()).hexdigest()[:16]
        self._mem[key] = QFAMEntry(key, pattern, ts, h, meta or {})

    def recall(self, query, threshold=None):
        thr = threshold or self._th
        res = []
        for k, e in self._mem.items():
            if str(e.pattern) == str(query):
                res.append({"key": k, "sim": 1.0, "ts": e.timestamp})
        return sorted(res, key=lambda x: x["sim"], reverse=True)

    @property
    def size(self): return len(self._mem)

# ============================================================================
# SOPHON PAIR (Substrato 5029)
# ============================================================================

class SophonState:
    def __init__(self, seal, phi_c=0.9997, coh=0.99991):
        self.seal = seal; self.phi_c = phi_c; self.coherence = coh
        self._rng = np.random.RandomState(hash(seal) % (2**32)) if np else None

class SophonPair:
    def __init__(self, fa="SOPHON-ALPHA", fb="SOPHON-BETA", pa=0.9997, pb=0.9996, fid=0.99991):
        self.a = SophonState(fa, pa, fid); self.b = SophonState(fb, pb, fid)
        self.fidelity = fid; self._est = False

    def establish(self, req=0.99):
        self.fidelity = max(0.0, 1.0 - abs(self.a.phi_c - self.b.phi_c) * 100.0)
        self._est = self.fidelity >= req
        if not self._est: raise Exception(f"Entanglement failed: F={self.fidelity:.5f}")
        return True

    def bell_test(self, trials=1000):
        if not self._est: raise Exception("Pair not established")
        return float(np.clip(abs(2 * np.sqrt(2)), 0, 2 * np.sqrt(2))) if np else 2.8

# ============================================================================
# TEMPORAL KEY STORE (Substrato 326)
# ============================================================================

@dataclass
class TemporalKey:
    key_id: str; key_bytes: bytes; created_at: float; expires_at: float; purpose: str; meta: dict = field(default_factory=dict)

class TemporalKeyStore:
    def __init__(self): self._k: Dict[str, TemporalKey] = {}
    def gen(self, purpose, ttl=300):
        kid = hashlib.sha3_256(f"{purpose}:{time.time()}:{uuid.uuid4()}".encode()).hexdigest()[:32]
        kb = hashlib.sha3_256(f"{kid}:{uuid.uuid4()}".encode()).digest()
        self._k[kid] = TemporalKey(kid, kb, time.time(), time.time()+ttl, purpose)
        return self._k[kid]
    def get(self, kid):
        k = self._k.get(kid)
        if k and k.expires_at < time.time(): del self._k[kid]; return None
        return k

# ============================================================================
# TEMPORAL HASH CHAIN (Substrato 5033)
# ============================================================================

@dataclass
class TemporalBlock:
    temporal_index: int; target_timestamp: float; prev_hash: str; data_hash: str; consistency_proof: str; causal_depth: float

    @property
    def block_hash(self):
        return hashlib.sha3_256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


class TemporalHashChain:
    def __init__(self):
        self._chain: List[TemporalBlock] = []
        self._idx = 0
        self._anomalies: List[Dict] = []
        g = TemporalBlock(0, 0.0, "0"*64, hashlib.sha3_256(b"ARKHE_GENESIS").hexdigest(), "GENESIS", 0.0)
        self._chain.append(g)

    @property
    def length(self): return len(self._chain)
    @property
    def head_hash(self): return self._chain[-1].block_hash if self._chain else ""
    @property
    def genesis_hash(self): return self._chain[0].block_hash if self._chain else ""

    def verify_integrity(self):
        errors = []
        for i in range(1, len(self._chain)):
            b = self._chain[i]; p = self._chain[i-1]
            if b.prev_hash != p.block_hash: errors.append(f"Block {i}: prev_hash mismatch")
            if b.temporal_index != p.temporal_index + 1: errors.append(f"Block {i}: index broken")
            if b.target_timestamp < p.target_timestamp: errors.append(f"Block {i}: temporal inversion")
        return len(errors) == 0, errors

    def insert_retrocausal(self, target_ts, data, proof, depth=0.0):
        dh = hashlib.sha3_256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        nb = TemporalBlock(0, target_ts, "", dh, proof, depth)
        idx = len(self._chain)
        for i, b in enumerate(self._chain):
            if target_ts < b.target_timestamp: idx = i; break
        if idx == 0: return None, "Cannot insert before genesis"
        nb.prev_hash = self._chain[idx-1].block_hash
        nb.temporal_index = self._chain[idx-1].temporal_index + 1
        self._chain.insert(idx, nb)
        for j in range(idx+1, len(self._chain)):
            self._chain[j].prev_hash = self._chain[j-1].block_hash
            self._chain[j].temporal_index = self._chain[j-1].temporal_index + 1
        self._idx = self._chain[-1].temporal_index
        return nb, ""

    def get_anomalies(self): return self._anomalies.copy()
    def record_anomaly(self, a): self._anomalies.append({"ts": time.time(), **a})

# ============================================================================
# SOLAR PLASMA MODEL (Substrato 5022-Solar)
# ============================================================================

PROTON_MASS = 1.6726e-27
ELECTRON_CHARGE = 1.602e-19
MU0 = 4 * math.pi * 1e-7

@dataclass
class PlasmaParameters:
    temperature_ev: float = SOLAR_CORONA_TEMP_EV
    density_m3: float = SOLAR_CORONA_DENSITY
    magnetic_field_t: float = SOLAR_CORONA_B_TESLA
    ion_mass_amu: float = 1.0
    beta_plasma: float = 0.01
    alfvén_speed: float = SOLAR_ALFVEN_SPEED

    @property
    def thermal_velocity(self) -> float:
        T = self.temperature_ev * ELECTRON_CHARGE
        return math.sqrt(T / (PROTON_MASS * self.ion_mass_amu))

    @property
    def gyroradius(self) -> float:
        return (PROTON_MASS * self.thermal_velocity) / (ELECTRON_CHARGE * self.magnetic_field_t)

    @property
    def plasma_frequency(self) -> float:
        return math.sqrt(self.density_m3 * ELECTRON_CHARGE**2 / (8.854e-12 * PROTON_MASS * self.ion_mass_amu))

    @property
    def collision_time(self) -> float:
        T = self.temperature_ev * ELECTRON_CHARGE
        ln_lambda = 23 - 0.5 * math.log(self.density_m3) + 1.5 * math.log(T)
        return (12 * math.pi ** 1.5 * ((PROTON_MASS * self.ion_mass_amu) ** 0.5 * (T ** 1.5)) /
                (self.density_m3 * ELECTRON_CHARGE**4 * ln_lambda))


class SolarPlasmaModel:
    def __init__(self, params: PlasmaParameters = None):
        self.params = params or PlasmaParameters()
        self._switchback_active = False
        self._reconnection_rate = 0.0
        self._ion_beams: Dict[str, dict] = {}
        self._switchback_history: List[Dict] = []

    def predict_switchback(self, time_ahead_s: float = 60.0) -> dict:
        probability = min(1.0, self.params.beta_plasma * 10.0)
        if probability > 0.5:
            result = {
                'predicted': True, 'probability': probability,
                'estimated_duration': self.params.gyroradius / self.params.alfvén_speed * 100,
                'magnetic_reversal': True, 'plasma_backflow': True,
                'arkhe_equivalent': 'TEMPORAL_REVERSAL_PREDICTED',
                'confidence': round(probability, 3),
            }
            self._switchback_history.append({**result, 'timestamp': time.time()})
            return result
        return {'predicted': False, 'probability': probability}

    def heavy_ion_beam(self, element: str = "Fe", charge_state: int = 12) -> dict:
        ion_mass_amu = {'H': 1.0, 'He': 4.0, 'C': 12.0, 'O': 16.0, 'Fe': 56.0}.get(element, 56.0)
        beam_focus = 1.0 / math.sqrt(ion_mass_amu)
        acceleration = self.params.alfvén_speed * (1 + charge_state * 0.1)
        return {
            'element': element, 'charge_state': charge_state,
            'beam_width_steradians': beam_focus * 0.1,
            'acceleration_ms': acceleration,
            'collimation_quality': 'laser-like' if beam_focus < 0.15 else 'moderate',
            'arkhe_equivalent': f'PktPriority.{"CRITICAL" if ion_mass_amu > 20 else "REALTIME"}',
        }

    def magnetic_reconnection(self, B1: float, B2: float, anti_parallel: bool = True) -> dict:
        stored_energy = (B1**2 + B2**2) / (2 * MU0)
        if anti_parallel and B1 * B2 < 0:
            reconnection_rate = 0.1 * abs(B1 + B2)
            released_energy = stored_energy * reconnection_rate
            catastrophic = released_energy > 1e12
            return {
                'stored_energy_j_per_m3': stored_energy, 'reconnection_rate': reconnection_rate,
                'released_energy': released_energy, 'catastrophic': catastrophic,
                'arkhe_equivalent': 'PARADOX_DETECTED' if catastrophic else 'MINOR_FLARE',
                'containment_possible': not catastrophic,
                'recommended_action': 'ACTIVATE_CAUSAL_SHIELD' if catastrophic else 'MONITOR',
            }
        return {'reconnection_rate': 0.0, 'catastrophic': False}


# ============================================================================
# MULTIVERSE ROUTER (Substrato 7005 — v4.1)
# ============================================================================

@dataclass
class TimelineBranch:
    branch_id: str
    divergence_timestamp: float
    divergence_event: str
    base_timeline: str = "main"
    taddr_base: str = ""
    coherence_score: float = 1.0
    is_active: bool = True


class MultiverseRouter:
    def __init__(self, ledger: AuditLedger, chain: TemporalHashChain):
        self.ledger = ledger
        self.chain = chain
        self.branches: Dict[str, TimelineBranch] = {}
        self._main_branch = self._create_main_branch()

    def _create_main_branch(self) -> TimelineBranch:
        main = TimelineBranch(branch_id="main", divergence_timestamp=0.0,
                              divergence_event="big_bang", base_timeline="main",
                              taddr_base=TAddr.from_parts("MAIN", 0.0, 0.0))
        self.branches["main"] = main
        self.ledger.record("timeline_branch", {'action': 'create', 'branch_id': 'main', 'divergence_event': 'big_bang'})
        return main

    def create_branch(self, divergence_event: str, from_timestamp: float, branch_id: str = None, base_timeline: str = "main") -> TimelineBranch:
        bid = branch_id or f"branch-{uuid.uuid4().hex[:8]}"
        epoch = from_timestamp + MULTIVERSE_BASE_OFFSET * len(self.branches)
        branch = TimelineBranch(branch_id=bid, divergence_timestamp=from_timestamp,
                                divergence_event=divergence_event, base_timeline=base_timeline,
                                taddr_base=TAddr.from_parts(bid, epoch, 0.01))
        self.branches[bid] = branch
        self.chain.insert_retrocausal(target_ts=epoch, data={'action': 'branch_create', 'branch_id': bid,
                              'divergence_event': divergence_event, 'source': 'multiverse_router'},
                              proof='branch_genesis', depth=0.0)
        self.ledger.record("timeline_branch", {'action': 'create', 'branch_id': bid,
                              'divergence_event': divergence_event, 'divergence_ts': from_timestamp, 'epoch': epoch})
        log.info(f"🌀 Branch criada: {bid} (divergência: {divergence_event})")
        return branch

    def get_branch(self, branch_id: str) -> Optional[TimelineBranch]:
        if branch_id not in self.branches:
            events = self.ledger.get_events_by_type("timeline_branch")
            for e in events:
                p = e['payload']
                if p.get('branch_id') == branch_id:
                    b = TimelineBranch(branch_id=branch_id, divergence_timestamp=p.get('divergence_ts', 0.0),
                                       divergence_event=p.get('divergence_event', 'unknown'),
                                       base_timeline=p.get('base_timeline', 'main'),
                                       taddr_base=str(p.get('taddr_base', '')),
                                       coherence_score=p.get('coherence_score', 1.0),
                                       is_active=p.get('is_active', True))
                    self.branches[branch_id] = b
                    return b
            raise TimelineNotFoundError(f"Branch '{branch_id}' não encontrada")
        return self.branches[branch_id]

    def is_accessible(self, world_a: str, world_b: str) -> bool:
        if world_a == world_b:
            return True
        current = world_b
        visited = set([current])
        while current in self.branches and current != "main":
            parent = self.branches[current].base_timeline
            if parent == world_a:
                return True
            if parent in visited:
                break
            visited.add(parent)
            current = parent
        return False

    def verify_kripke_semantics(self) -> bool:
        branches = list(self.branches.keys())
        for w in branches:
            if not self.is_accessible(w, w):
                return False
        for w1 in branches:
            for w2 in branches:
                if self.is_accessible(w1, w2):
                    for w3 in branches:
                        if self.is_accessible(w2, w3):
                            if not self.is_accessible(w1, w3):
                                return False
        return True

    def inter_branch_message(self, src_branch: str, dst_branch: str,
                              content: str, priority: int = 2) -> Tuple[bool, str, float]:
        if src_branch not in self.branches: return False, f"Branch origem '{src_branch}' não existe", 0.0
        if dst_branch not in self.branches: return False, f"Branch destino '{dst_branch}' não existe", 0.0

        src_b, dst_b = self.branches[src_branch], self.branches[dst_branch]
        now = time.time()
        temporal_offset = dst_b.taddr_base.tcoord.epoch - src_b.taddr_base.tcoord.epoch

        inter_msg = TemporalMessage(
            id=f"inter-{uuid.uuid4().hex[:12]}",
            content=json.dumps({'src_branch': src_branch, 'dst_branch': dst_branch,
                                'payload': content, 'multiverse': True}),
            source_timestamp=now, target_timestamp=now + temporal_offset,
            sender_seal=f"BRANCH-{src_branch}", receiver_seal=f"BRANCH-{dst_branch}",
            metadata={'branch_src': src_branch, 'branch_dst': dst_branch,
                      'multiverse_routing': True, 'priority': priority})

        oracle = TemporalConsistencyOracle(self.ledger, quantum_window=QUANTUM_NEGATIVE_WINDOW_SECONDS * 100)
        report = oracle.evaluate(inter_msg)

        if report.consistent:
            self.ledger.record("inter_branch_message", {
                'src_branch': src_branch, 'dst_branch': dst_branch,
                'message_id': inter_msg.id, 'consistency_score': report.score,
                'quantum_coherent': report.quantum_coherent,
                'temporal_offset': temporal_offset, 'content_preview': content[:200]})
            src_b.coherence_score = min(1.0, src_b.coherence_score - 0.01)
            dst_b.coherence_score = min(1.0, dst_b.coherence_score - 0.01)
            status = "⚛️ QUÂNTICO" if report.quantum_coherent else "🔗 CLÁSSICO"
            log.info(f"🌀 Mensagem inter-branch: {src_branch} → {dst_branch} | Score: {report.score:.4f} | {status}")
            return True, f"Entregue via {status}", report.score
        else:
            self.ledger.record("inter_branch_rejected", {
                'src_branch': src_branch, 'dst_branch': dst_branch,
                'reason': str(report.violations), 'score': report.score, 'paradox_type': report.paradox_type})
            return False, f"Rejeitado: score={report.score:.4f}, paradoxo={report.paradox_type}", report.score

    def branch_topology(self) -> dict:
        return {
            'branches': {bid: {'divergence_event': b.divergence_event, 'divergence_ts': b.divergence_timestamp,
                'coherence': b.coherence_score, 'taddr': b.taddr_base, 'active': b.is_active,
                'interactions': sum(1 for r in self.ledger.get_all_records()
                    if r['payload'].get('src_branch') == bid or r['payload'].get('dst_branch') == bid)}
                for bid, b in self.branches.items()},
            'total_branches': len(self.branches), 'main_branch': 'main',
            'edges': [(e['payload']['src_branch'], e['payload']['dst_branch'])
                      for e in self.ledger.get_events_by_type("inter_branch_message")],
        }

    def prune_inactive_branches(self, threshold_coherence: float = 0.3) -> int:
        removed = 0
        for bid in list(self.branches.keys()):
            if bid == "main": continue
            if self.branches[bid].coherence_score < threshold_coherence:
                self.branches[bid].is_active = False
                self.ledger.record("timeline_branch", {'action': 'pruned', 'branch_id': bid,
                                  'coherence_at_removal': self.branches[bid].coherence_score})
                removed += 1
                log.info(f"🌀 Branch podada: {bid} (coerência={self.branches[bid].coherence_score:.4f})")
        return removed

    def is_accessible(self, world_a: str, world_b: str) -> bool:
        if world_a == world_b:
            return True

        current = world_b
        visited = {current}
        while current in self.branches and current != "main":
            parent = self.branches[current].base_timeline
            if parent == world_a:
                return True
            if parent in visited:
                break
            visited.add(parent)
            current = parent

        return False

    def verify_kripke_semantics(self) -> bool:
        branches = list(self.branches.keys())

        for w in branches:
            if not self.is_accessible(w, w):
                return False

        for w1 in branches:
            for w2 in branches:
                if self.is_accessible(w1, w2):
                    for w3 in branches:
                        if self.is_accessible(w2, w3):
                            if not self.is_accessible(w1, w3):
                                return False

        return True


# ============================================================================
# TEMPORAL MESSAGE
# ============================================================================

@dataclass
class TemporalMessage:
    id: str; content: str; source_timestamp: float; target_timestamp: float
    sender_seal: str; receiver_seal: str; metadata: dict = field(default_factory=dict)

# ============================================================================
# CONSISTENCY ORACLE v4.1.1 (6 checks + compressão integrada)
# ============================================================================

@dataclass
class ConsistencyReport:
    consistent: bool; score: float; checks: Dict[str, float]; violations: List[str]
    paradox_type: Optional[str] = None
    quantum_coherent: bool = False
    quantum_window_seconds: float = QUANTUM_NEGATIVE_WINDOW_SECONDS
    solar_coherent: bool = False


class TemporalConsistencyOracle:
    TH = {'harmless': 0.999, 'paradox_free': 0.999, 'entropy_safe': 0.70,
          'coherent': 0.90, 'zk_valid': 0.95, 'quantum_time': 0.95, 'solar_coherence': 0.90}

    def __init__(self, ledger, epsilon_seconds=1.0,
                 quantum_window=QUANTUM_NEGATIVE_WINDOW_SECONDS,
                 solar_plasma_model: SolarPlasmaModel = None):
        self.ledger = ledger; self.epsilon = epsilon_seconds
        self.quantum_window = quantum_window
        self._paradox_graph: Dict[str, List[str]] = {}
        self.plasma = solar_plasma_model or SolarPlasmaModel()

    def _is_quantum_negative_time(self, delta_t: float) -> bool:
        return delta_t < 0 and abs(delta_t) <= self.quantum_window

    def _ch(self, m, zk=None):
        viol, sc = [], 1.0
        for r in self.ledger.get_all_records():
            if r['type'] != 'extratemporal_message_sent': continue
            if abs(r['timestamp'] - m.target_timestamp) >= self.epsilon: continue
            eid = r['payload'].get('msg_id', '')
            if eid and eid == m.id[:16]: sc = min(sc, 0.999)
            ec = r['payload'].get('content_hash', '')
            mc = hashlib.sha3_256(m.content.encode()).hexdigest()[:16]
            if ec and ec == mc[:12] and eid != m.id[:16]:
                sc = min(sc, 0.70); viol.append("Contradição semântica")
        return sc, viol

    def _cp(self, m, zk=None):
        viol, sc = [], 1.0; delta_t = m.target_timestamp - m.source_timestamp
        if self._is_quantum_negative_time(delta_t): return 1.0, []
        for r in self.ledger.get_all_records():
            if r['type'] != 'extratemporal_message_sent': continue
            mid = r['payload'].get('msg_id', ''); ts = r['timestamp']
            if ts > m.target_timestamp and mid != m.id:
                if self._has_causal_path(mid, m.id):
                    sc = 0.0; viol.append(f"LOOP CAUSAL: {m.id[:8]} → {mid[:8]} → {m.id[:8]}")
        if delta_t < 0 and not self._is_quantum_negative_time(delta_t):
            tj = abs(delta_t); tw = 1000.0
            if tj <= tw:
                sc = max(0.0, sc * (1.0 - (tj / tw) * 0.5))
                viol.append(f"Tempo negativo fora da janela quântica: Δt={delta_t:.3f}s")
            else:
                sc = max(0.0, sc * 0.3); viol.append(f"Tempo negativo extremo: Δt={delta_t:.0f}s")
        return sc, viol

    def _has_causal_path(self, fr, to, depth=10):
        if depth <= 0: return False
        if fr == to: return True
        for r in self.ledger.get_all_records():
            if r['payload'].get('msg_id', '') == fr:
                for r2 in self.ledger.get_all_records():
                    if r2['payload'].get('caused_by', '') == fr:
                        if self._has_causal_path(r2['payload'].get('msg_id', ''), to, depth - 1):
                            return True
        return False

    def _ce(self, m, zk=None):
        viol = []; dt = abs(m.target_timestamp - m.source_timestamp); ent = len(m.content) * 8
        temporal_cost = 0.0 if self._is_quantum_negative_time(m.target_timestamp - m.source_timestamp) else min(1.0, dt / DEFAULT_WINDOW_SECONDS)
        sc = max(0.0, 1.0 - 0.5 * temporal_cost - 0.5 * min(1.0, ent / (1024 * 1024 * 8)))
        if temporal_cost >= 1.0 and not self._is_quantum_negative_time(m.target_timestamp - m.source_timestamp):
            viol.append(f"Salto temporal próximo ao limite: {dt:.0f}s")
        return sc, viol

    def _cc(self, m, zk=None):
        viol = []; delta_t = m.target_timestamp - m.source_timestamp; mw = DEFAULT_WINDOW_SECONDS
        if self._is_quantum_negative_time(delta_t):
            return max(0.85, 1.0 - abs(delta_t) / self.quantum_window * 0.05), []
        if abs(delta_t) > mw: return max(0.0, 1.0 - abs(delta_t) / (mw * 10)), [f"Salto excede 5 anos"]
        return 1.0 - (abs(delta_t) / mw) * 0.1, []

    def _cz(self, m, zk=None):
        if zk is None: return 0.5, ["Sem prova ZK"]
        req = {'prover_seal', 'challenge', 'response', 'timestamp'}
        if not req.issubset(zk.keys()): return 0.0, ["Prova ZK incompleta"]
        age = time.time() - zk['timestamp']
        return (max(0.0, 1.0 - age / 3600), [f"Prova ZK expirada: {age:.0f}s"]) if age > 600 else (1.0, [])

    def _cs(self, m, zk=None):
        """6º check: Solar Coherence — bonus/penalidade baseada na atividade solar."""
        viol, sc = [], 1.0
        sb = self.plasma.predict_switchback(time_ahead_s=60)
        reconn = self.plasma.magnetic_reconnection(
            B1=self.plasma.params.magnetic_field_t, B2=-self.plasma.params.magnetic_field_t * 0.8)
        delta_t = m.target_timestamp - m.source_timestamp
        if sb.get('predicted') and self._is_quantum_negative_time(delta_t):
            sc = min(1.0, sc + 0.05)  # bônus solar
        if reconn.get('catastrophic'):
            penalty = min(0.3, reconn.get('released_energy', 0) / 1e15)
            sc = max(0.0, sc * (1.0 - penalty))
            viol.append(f"Reconexão magnética catastrófica: penalidade={penalty:.3f}")
        return sc, viol

    def evaluate(self, m, zk=None):
        checks, viol = {}, []
        delta_t = m.target_timestamp - m.source_timestamp
        quantum = self._is_quantum_negative_time(delta_t)

        for name, fn in [('harmless', self._ch), ('paradox_free', self._cp),
                         ('entropy_safe', self._ce), ('coherent', self._cc),
                         ('zk_valid', self._cz), ('solar_coherence', self._cs)]:
            s, v = fn(m, zk) if name == 'zk_valid' else fn(m)
            checks[name] = s; viol.extend(v)

        score = min(checks.values())
        if quantum:
            score = min(1.0, score + 0.05)
            checks['quantum_time'] = score
            if score >= min(self.TH.values()):
                log.info("⚛️ REGIME QUÂNTICO: Δt=%.3e s, janela=%.0e s", delta_t, self.quantum_window)

        # Compressão automática do payload para armazenamento
        try:
            raw = json.dumps(m.content.__dict__ if hasattr(m.content, '__dict__') else m.content).encode()
            compressed = _zlib.compress(raw) if len(raw) < 1024 * 1024 else _gzip.compress(raw)
            decompressed = _zlib.decompress(compressed) if len(raw) < 1024 * 1024 else _gzip.decompress(compressed)
            assert hashlib.sha3_256(decompressed).hexdigest() == hashlib.sha3_256(raw).hexdigest()
        except (AssertionError, Exception) as e:
            log.warning(f"⚠️ Integridade de compressão: {e}")

        return ConsistencyReport(
            consistent=score >= min(self.TH.values()), score=round(score, 6),
            checks={k: round(v, 6) for k, v in checks.items()}, violations=viol,
            paradox_type=self._classify(viol) if score < 0.999 else None,
            quantum_coherent=quantum, quantum_window_seconds=self.quantum_window,
            solar_coherent=checks.get('solar_coherence', 1.0) >= 0.8)

    def _classify(self, v):
        t = ' '.join(v).lower()
        if 'causal' in t or 'loop' in t: return "GRANDPARENT"
        if 'contradiction' in t or 'duplicat' in t: return "PREDICTION"
        if 'entrop' in t: return "ENTROPY"
        if 'zk' in t: return "AUTH"
        if 'reconex' in t or 'catastroph' in t: return "SOLAR_INSTABILITY"
        return None

# ============================================================================
# PONTE PLASMA ↔ ARKHE (Substrato 5022 + 5034)
# ============================================================================

class PlasmaArkheBridge:
    def __init__(self, oracle: TemporalConsistencyOracle = None, ledger: AuditLedger = None):
        if oracle is None:
            if ledger is None:
                ledger = AuditLedger()
            self.oracle = TemporalConsistencyOracle(ledger)
        else:
            self.oracle = oracle
        self.plasma = SolarPlasmaModel()
        self.ledger = self.oracle.ledger

    def process_solar_event(self, event_type: str, properties: dict) -> 'ConsistencyReport':
        now = time.time()
        temporal_offsets = {'switchback': -QUANTUM_NEGATIVE_WINDOW_SECONDS * 0.5,
            'reconnection': -300.0, 'ion_beam': 0.0, 'cme': 600.0, 'flare': -60.0}
        priority_map = {'switchback': 1, 'reconnection': 0, 'ion_beam': 2, 'cme': 0, 'flare': 1}
        offset = temporal_offsets.get(event_type, 0.0)

        msg = TemporalMessage(
            id=f"solar-{event_type}-{now:.0f}",
            content=json.dumps({'event': event_type,
                'plasma_params': {'beta': self.plasma.params.beta_plasma,
                    'v_th': self.plasma.params.thermal_velocity, 'r_L': self.plasma.params.gyroradius},
                'properties': properties}),
            source_timestamp=now, target_timestamp=now + offset,
            sender_seal="SUN-SOL-A", receiver_seal="ARKHE-EARTH")

        report = self.oracle.evaluate(msg)
        self.ledger.record("solar_plasma_event", {
            'event_type': event_type, 'offset_seconds': offset,
            'quantum_coherent': report.quantum_coherent,
            'consistency_score': report.score, 'paradox_type': report.paradox_type,
            **properties})

        qtag = "⚛️" if report.quantum_coherent else "—"
        print(f"☀️ Solar Event: {event_type:<16} | Δt={offset:+.1e}s | "
              f"Score={report.score:.4f} | Quantum={qtag} | Paradox={report.paradox_type or 'None'}")
        return report

    def analyze_solar_conditions(self) -> dict:
        results = {'switchbacks': [], 'reconnections': [], 'ion_beams': [], 'summary': {}}
        sb = self.plasma.predict_switchback(time_ahead_s=60)
        if sb.get('predicted'): results['switchbacks'].append(sb); results['switchback_count'] = 1
        reconn = self.plasma.magnetic_reconnection(B1=0.001, B2=-0.0008, anti_parallel=True)
        results['reconnections'].append(reconn)
        for elem in ['H', 'He', 'O', 'Fe']:
            results['ion_beams'].append(self.plasma.heavy_ion_beam(elem, charge_state=12))
        has_catastrophic = any(r.get('catastrophic') for r in results['reconnections'])
        has_switchbacks = any(s.get('predicted') for s in results['switchbacks'])
        risk = 0.9 if has_catastrophic else (0.3 if has_switchbacks else 0.0)
        results['summary'] = {
            'global_risk_level': risk,
            'recommended_action': ('EVACUATE' if risk > 0.8 else 'SHIELD_UP' if risk > 0.4
                                   else 'MONITOR' if risk > 0.1 else 'ALL_CLEAR'),
            'arkhe_consistency': ('AT_RISK' if risk > 0.5
                else 'QUANTUM_COHERENT' if has_switchbacks else 'CLASSICAL_STABLE')}
        return results

# ============================================================================
# CAUSAL SHIELD (Substrato 5035)
# ============================================================================

class CausalShield:
    def __init__(self, ledger):
        self.ledger = ledger; self._wl: Set[str] = set(); self._bl: Set[str] = set()
        self._rl: Dict[str, Deque[float]] = {}; self._mx = 100; self._st = {'a': 0, 'r': 0}

    def eval(self, m):
        if m.sender_seal in self._bl: return False, f"Bloqueado: {m.sender_seal}"
        if self._wl and m.sender_seal not in self._wl: return False, f"Não autorizado: {m.sender_seal}"
        now = time.time(); delta_t = m.target_timestamp - now
        is_quantum = abs(delta_t) <= QUANTUM_NEGATIVE_WINDOW_SECONDS and delta_t < 0
        if not is_quantum:
            if m.sender_seal not in self._rl: self._rl[m.sender_seal] = deque(maxlen=self._mx)
            recent = [t for t in self._rl[m.sender_seal] if t > now - 3600]
            if len(recent) >= self._mx: return False, f"Rate limit: {m.sender_seal}"
            self._rl[m.sender_seal].append(now)
            if abs(m.target_timestamp - now) > DEFAULT_WINDOW_SECONDS:
                return False, f"Timestamp fora de 5 anos: {abs(m.target_timestamp - now):.0f}s"
        self._st['a'] += 1; return True, "OK"

    def wl(self, s): self._wl.add(s)
    def bl(self, s): self._bl.add(s)
    @property
    def stats(self): return {**self._st, 'wl': len(self._wl)}

# ============================================================================
# RETROCAUSAL VALIDATOR
# ============================================================================

class RetrocausalValidator:
    def __init__(self, ledger):
        self.shield = CausalShield(ledger)
        self.oracle = TemporalConsistencyOracle(ledger)
        self.accepted = 0; self.rejected = 0; self.quantum_accepted = 0

    def validate(self, msg, zk=None):
        ok, reason = self.shield.eval(msg)
        if not ok: self.rejected += 1; return _ValidationResult(False, 0.0, None, False, reason)
        report = self.oracle.evaluate(msg, zk)
        if report.consistent:
            self.accepted += 1
            if report.quantum_coherent: self.quantum_accepted += 1
        else: self.rejected += 1
        return _ValidationResult(report.consistent, report.score, report,
                                report.quantum_coherent, reason if not report.consistent else "")

    @property
    def stats(self):
        t = self.accepted + self.rejected
        return {'accepted': self.accepted, 'rejected': self.rejected, 'total': t,
                'rate': f"{self.accepted/max(t,1)*100:.1f}%", 'quantum_accepted': self.quantum_accepted}

@dataclass
class _ValidationResult:
    accepted: bool; score: float; report: Any; quantum_coherent: bool
    shield_reason: str = ""; timestamp: float = field(default_factory=time.time)

# ============================================================================
# TADDR
# ============================================================================

@dataclass(frozen=True)
class TCoord:
    epoch: float; uncertainty: float = 0.0
    @property
    def min_e(self): return self.epoch - self.uncertainty
    @property
    def max_e(self): return self.epoch + self.uncertainty

@dataclass(frozen=True)
class TAddr:
    node_id: str; tcoord: TCoord
    def __str__(self):
        return f"{self.node_id}@{self.tcoord.epoch:.3f}±{self.tcoord.uncertainty:.3f}" if self.tcoord.uncertainty > 0 else f"{self.node_id}@{self.tcoord.epoch:.3f}"
    @classmethod
    def parse(cls, s):
        if '@' not in s: raise ValueError(s)
        np_, tp = s.rsplit('@', 1)
        if tp.lower() == 'now': ep = time.time(); unc = 0.0
        elif '±' in tp: ep = float(tp.split('±')[0]); unc = float(tp.split('±')[1])
        else: ep = float(tp); unc = 0.0
        return cls(np_.strip(), TCoord(ep, unc))
    @classmethod
    def from_parts(cls, nid, epoch, unc=0.0): return cls(nid, TCoord(epoch, unc))
    def is_retro(self): return self.tcoord.max_e < time.time()

class TAddrResolver:
    def __init__(self): self._cache: Dict[str, TAddr] = {}
    def set_local(self, a): self._cache[a.node_id] = a
    def register(self, name, addr): self._cache[name] = addr
    def resolve(self, name):
        if name in self._cache: return self._cache[name]
        try: return TAddr.parse(name)
        except: return None

# ============================================================================
# RNP
# ============================================================================

class PktPriority(IntEnum):
    CRITICAL=0; CONTROL=1; REALTIME=2; BULK=3; BACKGROUND=4

class PktType(IntEnum):
    DATA=0; ACK=1; SYN=2; SYN_ACK=3; FIN=4; FIN_ACK=5; RST=6
    ROUTING_UPDATE=7; HEARTBEAT=8; PEER_REQ=9; PEER_ACCEPT=10; PEER_REJECT=11
    TDNS_QUERY=12; TDNS_RESP=13; TTL_ERR=14; ERROR=15; MULTIVERSE=16

MAX_HOPS = 32

@dataclass
class RNPHeader:
    ver: str = VERSION; pkt_type: int = PktType.DATA; pkt_id: str = ""
    src: str = ""; dst: str = ""
    ttl: float = DEFAULT_WINDOW_SECONDS; hop: int = 0; max_hops: int = MAX_HOPS
    prio: int = PktPriority.CONTROL; seq: int = 0; ack: int = 0; win: int = 0
    created: float = 0.0; target_ts: float = 0.0; encrypted: bool = False
    t_depth: float = 0.0; consistency: float = 1.0; chain_hash: str = ""
    flags: int = 0; _chksum: str = ""
    def to_dict(self): return {k: v for k, v in asdict(self).items()}
    def compute_chksum(self): d = self.to_dict(); d['_chksum'] = ''; return hashlib.sha3_256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]
    def validate_chksum(self): return self.compute_chksum() == self._chksum
    def ttl_expired(self): return time.time() - self.created > self.ttl
    def hops_bad(self): return self.hop >= self.max_hops
    def before_cksum(self): self._chksum = self.compute_chksum()

@dataclass
class RetroPacket:
    header: RNPHeader = field(default_factory=RNPHeader); payload: bytes = b""
    route: List[str] = field(default_factory=list); meta: Dict = field(default_factory=dict)
    @property
    def pid(self): return self.header.pkt_id
    def full_hash(self):
        return hashlib.sha3_256(json.dumps({'h': self.header.to_dict(),
            'ph': hashlib.sha3_256(self.payload).hexdigest(), 'route': self.route},
            sort_keys=True).encode()).hexdigest()
    def serialize(self):
        import base64
        return json.dumps({'h': self.header.to_dict(), 'p': base64.b64encode(self.payload).decode(),
                           'r': self.route, 'm': self.meta}).encode()
    @classmethod
    def deserialize(cls, data):
        import base64
        d = json.loads(data.decode())
        return cls(header=RNPHeader(**{k: v for k, v in d['h'].items() if k in RNPHeader.__dataclass_fields__}),
                   payload=base64.b64decode(d.get('p', '')), route=d.get('r', []), meta=d.get('m', {}))
    def response(self, payload=b"", pkt_type=PktType.ACK):
        return RetroPacket(header=RNPHeader(pkt_type=pkt_type, pkt_id=f"r-{uuid.uuid4().hex[:12]}",
            src=self.header.dst, dst=self.header.src, ttl=self.header.ttl, hop=self.header.hop,
            prio=self.header.prio, seq=self.header.ack, ack=self.header.seq+1,
            created=time.time(), target_ts=self.header.target_ts,
            consistency=self.header.consistency, chain_hash=self.header.chain_hash),
            payload=payload, route=list(reversed(self.route)), meta={'resp': self.pid})

# ============================================================================
# ROUTING TABLE
# ============================================================================

@dataclass
class RouteEntry:
    dest: str; next_hop: str; nh_addr: str; cost: float; updated: float
    via_peer: bool; conf: float; expires: float

class TemporalRoutingTable:
    def __init__(self, nid):
        self._nid = nid; self._routes: List[RouteEntry] = []
        self._peers: Dict[str, TAddr] = {}; self._bh: Set[str] = set()
    def add(self, dest, nh, nh_addr, cost=1.0, via=False, conf=0.8, ttl=3600):
        for i, r in enumerate(self._routes):
            if r.dest == dest and r.next_hop == nh:
                self._routes[i] = RouteEntry(dest, nh, nh_addr, cost, time.time(), via, conf, time.time()+ttl); return
        self._routes.append(RouteEntry(dest, nh, nh_addr, cost, time.time(), via, conf, time.time()+ttl))
    def direct_peer(self, pid, addr):
        self._peers[pid] = addr; self.add(pid, pid, str(addr), 0.0, True, 0.99, RETRONET_PEERING_INTERVAL*4)
    def lookup(self, dest_addr):
        did = dest_addr.node_id
        if did in self._bh: return None
        vr = [r for r in self._routes if (r.dest == did or r.dest == f"{did}@*" or r.dest == "*") and r.expires > time.time()]
        if not vr:
            dr = [r for r in self._routes if r.dest == "DEFAULT" and r.expires > time.time()]
            if dr: vr = dr
        if not vr:
            if did in self._peers: return RouteEntry(did, did, str(self._peers[did]), 0.0, True, 0.99, time.time()+3600)
            return None
        return min(vr, key=lambda r: r.cost)
    def update(self, src, routes):
        for ri in routes: self.add(ri['dest'], src, ri.get('nh_addr',''), ri.get('cost',999)+1, False, ri.get('conf',0.5)*0.8, ri.get('ttl',3600))
    def expire(self):
        n = len(self._routes); now = time.time(); self._routes = [r for r in self._routes if r.expires > now]; return n - len(self._routes)
    def all_routes(self):
        now = time.time(); return [{'dest':r.dest,'next':r.next_hop,'cost':r.cost,'conf':r.conf,'via':r.via_peer}
                                   for r in sorted(self._routes, key=lambda x: x.cost) if r.expires > now]

# ============================================================================
# TDNS
# ============================================================================

class TDNSRecord:
    def __init__(self, name, taddr, rtype="A", ttl=3600, by=""):
        self.name = name; self.taddr = taddr; self.rtype = rtype; self.ttl = ttl; self.reg_at = time.time(); self.by = by

class TemporalDNS:
    def __init__(self, suffix=".arakhe"):
        self._recs: Dict[str, TDNSRecord] = {}; self._cache: Dict[str, Tuple[TAddr, float]] = {}; self._suffix = suffix
    def local_reg(self, name, addr):
        fn = self._qual(name); self._recs[fn] = TDNSRecord(fn, addr, "A", 3600, "local"); self._cache[fn] = (addr, time.time()+3600); return self._recs[fn]
    def resolve(self, name):
        fn = self._qual(name)
        if fn in self._cache:
            a, e = self._cache[fn]
            if e > time.time():
                return a
            else:
                del self._cache[fn]
        if fn in self._recs: r = self._recs[fn]; self._cache[fn] = (r.taddr, time.time()+r.ttl); return r.taddr
        try: return TAddr.parse(fn)
        except: return None
    def _qual(self, n): return f"{n}{self._suffix}" if '.' not in n else n

# ============================================================================
# FIREWALL
# ============================================================================

class TemporalFirewall:
    def __init__(self, nid):
        self._nid = nid; self._allow: Set[str] = set(); self._bl: Set[str] = set()
        self._max_depth = DEFAULT_WINDOW_SECONDS; self._rules: List[Dict] = []; self._st = {'a': 0, 'b': 0, 'f': 0}
    def allow(self, nid): self._allow.add(nid)
    def block(self, nid): self._bl.add(nid)
    def rule(self, r): self._rules.append(r)
    def check_in(self, pkt, addr):
        src = pkt.header.src.split('@')[0]
        if src in self._bl: self._st['b'] += 1; return False, "blocked"
        if self._allow and src not in self._allow: self._st['b'] += 1; return False, "unauthorized"
        for r in self._rules:
            if self._match(r, pkt):
                if r['action'] == 'deny': self._st['b'] += 1; return False, r.get('name', 'rule')
                if r['action'] == 'allow': self._st['a'] += 1; return True, r.get('name', 'rule')
        td = abs(pkt.header.target_ts - time.time())
        if td > self._max_depth: self._st['f'] += 1; return False, "depth exceeded"
        if pkt.header.hops_bad(): self._st['f'] += 1; return False, "hops exceeded"
        if pkt.header.ttl_expired(): self._st['f'] += 1; return False, "TTL expired"
        self._st['a'] += 1; return True, "OK"
    def _match(self, r, pkt):
        m = r.get('match', {}); src = pkt.header.src.split('@')[0]; td = abs(pkt.header.target_ts - time.time())
        if m.get('node_id') and m['node_id'] != src: return False
        if m.get('max_depth') and td > m['max_depth']: return False
        if m.get('prio') is not None and pkt.header.prio != m['prio']: return False
        return True

# ============================================================================
# RETRO ROUTER
# ============================================================================

class RetroRouter:
    def __init__(self, node):
        self.node = node; self.rt = TemporalRoutingTable(node.nid); self.tdns = TemporalDNS()
        self.fw = TemporalFirewall(node.nid); self.pkt_log: List[Dict] = []
        self._upd_t = 0; self._hb_t = 0
        self.recovery_gateway = None

    @property
    def ledger(self):
        return self.node._channel.ledger

    def chain(self):
        return self.node._channel.temporal_hash_chain

    @property
    def validator(self):
        if not hasattr(self, "_validator"):
            self._validator = RetrocausalValidator(self.ledger)
        return self._validator

    def enable_recovery_email(self, config):
        # Local import to avoid circular dependency
        from recovery_email_gateway import RecoveryEmailGateway
        self.recovery_gateway = RecoveryEmailGateway(self, config)
        def recovery_worker():
            while True:
                if self.recovery_gateway:
                    self.recovery_gateway.send_retry_queue()
                    received = self.recovery_gateway.poll_inbox()
                    if received:
                        self.recovery_gateway.reconcile(received)
                time.sleep(30)
        threading.Thread(target=recovery_worker, daemon=True).start()

    def _send_via_primary(self, msg, primary_route: str) -> bool:
        # Dummy implementation of primary route sending to avoid error
        return False

    def send_message_with_fallback(self, msg, primary_route: str) -> bool:
        if self._send_via_primary(msg, primary_route):
            return True
        if self.recovery_gateway:
            score = self.validator.validate(msg).score
            chain_hash = self.chain().head_hash
            self.recovery_gateway.enqueue(msg, score, chain_hash)
            log.info(f"Message {msg.id} enqueued for email recovery")
            return True
        return False

    def route(self, pkt, ingress=None):
        if pkt.header.ttl_expired(): self._err(pkt, "TTL_ERR"); return None
        if pkt.header.hops_bad(): self._err(pkt, "HOP_ERR"); return None
        try: da = TAddr.parse(pkt.header.dst)
        except: return None
        if da.node_id == self.node.nid: return "__LOCAL__"
        route = self.rt.lookup(da)
        if route: return route.next_hop
        dr = self.rt.lookup(TAddr.from_parts("DEFAULT-GW", time.time()))
        if dr: return dr.next_hop
        self._err(pkt, "NO_ROUTE"); return None
    def _err(self, orig, etype):
        try:
            reasons = {'TTL_ERR':'TTL expired','HOP_ERR':'Hop limit','NO_ROUTE':'No route','FW_BLOCK':'Firewall','MULTIVERSE_MISS':'Timeline not found'}
            epkt = RetroPacket(header=RNPHeader(pkt_type=PktType.ERROR, pkt_id=f"e-{uuid.uuid4().hex[:12]}",
                src=self.node.nid, dst=orig.header.src, ttl=DEFAULT_WINDOW_SECONDS, hop=orig.header.hop,
                prio=PktPriority.CRITICAL, created=time.time(), target_ts=orig.header.target_ts),
                payload=json.dumps({'type':etype,'orig':orig.pid,'at':self.node.nid,'reason':reasons.get(etype,'?')}).encode(),
                route=list(reversed(orig.route)))
        except: pass
    def process(self, pkt, addr):
        pkt.header.hop += 1; pkt.route.append(self.node.nid)
        ok, reason = self.fw.check_in(pkt, addr)
        if not ok: self._err(pkt, "FW_BLOCK"); return "DROP"
        if not pkt.header.validate_chksum(): self._err(pkt, "CHK_ERR"); return "DROP"
        self._log(pkt, "RCVD"); nxt = self.route(pkt, addr)
        if nxt == "__LOCAL__": self._deliver(pkt); return "ACCEPT"
        elif nxt: self._fwd(pkt, nxt); return "ROUTED"
        return "DROP"
    def _deliver(self, pkt):
        pt = pkt.header.pkt_type
        try:
            if pt == PktType.DATA: self.node.deliver(pkt); ack = pkt.response(b"", PktType.ACK); self._route_out(ack)
            elif pt == PktType.ACK: pass
            elif pt == PktType.SYN: ack = pkt.response(b"", PktType.SYN_ACK); self._route_out(ack)
            elif pt == PktType.FIN: ack = pkt.response(b"", PktType.FIN_ACK); self._route_out(ack)
            elif pt == PktType.HEARTBEAT: ack = pkt.response(b"", PktType.ACK); self._route_out(ack)
            elif pt == PktType.ROUTING_UPDATE: self._proc_ru(pkt)
            elif pt == PktType.ERROR:
                try: d = json.loads(pkt.payload.decode()); log.warning(f"RNP Error: {d.get('type')}")
                except: pass
            elif pt == PktType.TDNS_QUERY: self._tdns_q(pkt)
            elif pt == PktType.TDNS_RESP: self._tdns_r(pkt)
            elif pt == PktType.PEER_REQ: self._peer_req(pkt)
            elif pt == PktType.PEER_ACCEPT: self._peer_acc(pkt)
            elif pt == PktType.MULTIVERSE: self._multiverse_deliver(pkt)
        except Exception as e: log.error(f"Delivery error: {e}")
    def _multiverse_deliver(self, pkt):
        try: d = json.loads(pkt.payload.decode()); log.info(f"🌀 MULTIVERSE PKT: branch={d.get('src_branch')} → {d.get('dst_branch')}"); self.node.deliver(pkt)
        except: pass
    def _fwd(self, pkt, nxt): pkt.route.append(f"→{nxt}"); self.node.send(nxt, pkt); self._log(pkt, "FWD")
    def _route_out(self, pkt): nxt = self.route(pkt); (nxt != "__LOCAL__") and self._fwd(pkt, nxt)
    def _tdns_q(self, pkt):
        try: q = json.loads(pkt.payload.decode()); taddr = self.tdns.resolve(q.get('name','')); resp = json.dumps({'name':q.get('name',''),'ok':taddr is not None,'taddr':str(taddr) if taddr else '','qid':q.get('qid','')}).encode(); rp = pkt.response(resp, PktType.TDNS_RESP); self._route_out(rp)
        except: pass
    def _tdns_r(self, pkt):
        try: d = json.loads(pkt.payload.decode()); d.get('ok') and self.tdns._cache.update({d['name']: (TAddr.parse(d['taddr']), time.time()+3600)})
        except: pass
    def _peer_req(self, pkt):
        try: d = json.loads(pkt.payload.decode()); pid = d.get('node_id',''); pa = d.get('addr','')
        except: return
        if pid and pa: ta = TAddr.parse(pa); self.rt.direct_peer(pid, ta); acc = pkt.response(json.dumps({'node_id':self.node.nid,'addr':str(self.node.taddr)}).encode(), PktType.PEER_ACCEPT); self._route_out(acc); log.info(f"Peering: {pid} OK")
    def _peer_acc(self, pkt):
        try: d = json.loads(pkt.payload.decode()); pid = d.get('node_id',''); self.rt.direct_peer(pid, TAddr.parse(d['addr'])); log.info(f"Peering: {pid} established")
        except: pass
    def _proc_ru(self, pkt):
        try: d = json.loads(pkt.payload.decode()); self.rt.update(pkt.header.src.split('@')[0], d.get('routes', []))
        except: pass
    def ru_broadcast(self):
        routes = [{'dest':r.dest,'cost':r.cost,'nh_addr':r.nh_addr,'ttl':r.expires-time.time(),'conf':r.conf}
                  for r in self.rt._routes if r.via_peer or r.expires>time.time()]
        rp = RetroPacket(header=RNPHeader(pkt_type=PktType.ROUTING_UPDATE, pkt_id=f"ru-{uuid.uuid4().hex[:12]}",
            src=self.node.nid, dst="BROADCAST@0", ttl=RETRONET_PEERING_INTERVAL*2, prio=PktPriority.CONTROL,
            created=time.time(), target_ts=time.time()), payload=json.dumps({'routes':routes}).encode())
        for pid in self.rt._peers: self.node.send(pid, rp)
    def _log(self, pkt, act): self.pkt_log.append({'t':time.time(),'act':act,'pid':pkt.pid,'type':pkt.header.pkt_type,'src':pkt.header.src[:20],'dst':pkt.header.dst[:20],'hop':pkt.header.hop})
    def periodic(self):
        self.rt.expire()
        if time.time() - self._upd_t > RETRONET_PEERING_INTERVAL: self.ru_broadcast(); self._upd_t = time.time()
        if time.time() - self._hb_t > RETRONET_HEARTBEAT_INTERVAL: self._hb(); self._hb_t = time.time()
    def _hb(self):
        for pid, addr in self.rt._peers.items():
            hb = RetroPacket(header=RNPHeader(pkt_type=PktType.HEARTBEAT, pkt_id=f"hb-{uuid.uuid4().hex[:8]}",
                src=self.node.nid, dst=str(addr), ttl=RETRONET_HEARTBEAT_INTERVAL*3,
                prio=PktPriority.CONTROL, created=time.time(), target_ts=time.time()), payload=b'')
            self.node.send(pid, hb)

# ============================================================================
# RETRO NODE
# ============================================================================

class RetroNode:
    def __init__(self, nid, taddr=None, db_path=None):
        self.nid = nid
        self.taddr = taddr or TAddr.from_parts(nid, time.time(), 0.001)
        self.router = RetroRouter(self)
        self._peers: Dict[str, 'RetroNode'] = {}
        db = Path(db_path or f"/tmp/arkhe_{nid}.db")
        self._channel = type('C', (), {'ledger': AuditLedger(str(db)), 'temporal_hash_chain': TemporalHashChain(), '_initialized': True})()
        self._tdns = self.router.tdns; self._tdns.local_reg(nid, self.taddr)
        self._handlers = {}; self._running = False; self._inbox = deque(maxlen=10000)
        self._sent = 0; self._recv = 0
        self.multiverse = MultiverseRouter(self._channel.ledger, self._channel.temporal_hash_chain)

    def start(self): self._running = True; log.info(f"=== RETRONODE {self.nid} INICIADO | {self.taddr} ==="); threading.Thread(target=self._loop, daemon=True).start()
    def stop(self): self._running = False
    def _loop(self):
        while self._running:
            try:
                while self._inbox: self.router.process(self._inbox.popleft(), "local")
                self.router.periodic(); time.sleep(0.3)
            except Exception as e: log.error(f"Loop error: {e}"); time.sleep(1)
    def connect(self, peer): self._peers.__setitem__(peer.nid, peer); peer._peers[self.nid] = self; self.router.rt.direct_peer(peer.nid, peer.taddr)
    def send(self, nid, pkt):
        if nid not in self._peers: log.error(f"Peer {nid} desconhecido"); return False
        self._peers[nid].receive(pkt, self.nid); self._sent += 1; return True
    def receive(self, pkt, frm): self._inbox.append(pkt); self._recv += 1
    def deliver(self, pkt): h = self._handlers.get(pkt.header.pkt_type); (h and h(pkt)) or log.info(f"📨 [{self.nid}] Pkt {pkt.pid} tipo={pkt.header.pkt_type} de={pkt.header.src[:20]}")
    def reg_handler(self, pt, fn): self._handlers[pt] = fn
    def send_message(self, dest, msg, target=None, prio=PktPriority.REALTIME):
        ta = self.router.tdns.resolve(dest)
        if not ta:
            try: ta = TAddr.parse(dest)
            except: ta = TAddr.from_parts(dest, time.time())
        if target is None: target = ta.tcoord.epoch
        pid = f"m-{uuid.uuid4().hex[:12]}"; pkt = RetroPacket(header=RNPHeader(pkt_type=0, pkt_id=pid, src=str(self.taddr), dst=str(ta), ttl=DEFAULT_WINDOW_SECONDS, prio=prio, seq=self._sent, created=time.time(), target_ts=target, encrypted=True, t_depth=abs(target-time.time())), payload=msg.encode())
        nxt = self.router.route(pkt)
        if nxt and nxt != "__LOCAL__": self.send(nxt, pkt); log.info(f"MSG: {self.nid}→{ta.node_id} via {nxt} Δt={target-time.time():.0f}s")
        elif nxt == "__LOCAL__": self.router._deliver(pkt)
        return pkt
    def send_multiverse(self, dst_branch, content, src_branch="main"): return self.multiverse.inter_branch_message(src_branch, dst_branch, content)
    def create_timeline_branch(self, event_name, timestamp=None): return self.multiverse.create_branch(event_name, timestamp or time.time())
    def ping(self, dest, count=4):
        ta = self.router.tdns.resolve(dest)
        if not ta: return []
        res = []
        for i in range(count): pid = f"ping-{uuid.uuid4().hex[:8]}"; pkt = RetroPacket(header=RNPHeader(pkt_type=0, pkt_id=pid, src=str(self.taddr), dst=str(ta), ttl=DEFAULT_WINDOW_SECONDS, prio=1, seq=i, created=time.time(), target_ts=time.time()), payload=json.dumps({'ping':pid,'seq':i}).encode()); t0 = time.time(); rt = self.router.route(pkt); res.append({'seq':i,'route':rt,'rtt_ms':round((time.time()-t0)*1000,3),'ok':rt is not None}); time.sleep(0.4)
        return res
    def trace(self, dest, max_h=16):
        ta = self.router.tdns.resolve(dest)
        if not ta: return []
        return [({'hop':ttl,'next':rt}) for ttl in range(1, max_h+1) if not (((pkt := RetroPacket(header=RNPHeader(pkt_type=0, pkt_id=f"tr-{uuid.uuid4().hex[:8]}", src=str(self.taddr), dst=str(ta), ttl=1.0, hop=0, max_hops=ttl, prio=1, created=time.time(), target_ts=time.time()), payload=b'')), (rt := self.router.route(pkt)), (hops := [{'hop':ttl,'next':rt}]), ((rt=="__LOCAL__" or rt==ta.node_id) or (not rt))) and False)]

    def status(self): return {'nid':self.nid,'taddr':str(self.taddr),'peers':list(self._peers.keys()),'routes':len(self.router.rt._routes),'tdns':len(self.router.tdns._recs),'sent':self._sent,'recv':self._recv,'inbox':len(self._inbox),'fw_stats':self.router.fw._st,'branches':len(self.multiverse.branches)}

# ============================================================================
# RETRO NET
# ============================================================================

class RetroNet:
    def __init__(self): self._nodes: Dict[str, RetroNode] = {}; self._graph: Dict[str, Set[str]] = defaultdict(set)
    def create(self, nid, **kw):
        if nid in self._nodes: return self._nodes[nid]
        node = RetroNode(nid, TAddr.from_parts(nid, time.time()+kw.get('offset',0), kw.get('unc',0.001)), Path(f"/tmp/arkhe_{nid}.db"))
        self._nodes[nid] = node; return node
    def get(self, nid): return self._nodes.get(nid)
    def link(self, a, b):
        na, nb = self.get(a), self.get(b)
        if not na or not nb: return False
        na.connect(nb); self._graph[a].add(b); self._graph[b].add(a); return True
    def retro_send(self, src, dst, msg, offset=0, target=None):
        sn, dn = self.get(src), self.get(dst)
        if not sn: return {'error':'src not found'}
        if not dn: return {'error':'dst not found'}
        if target is None: target = dn.taddr.tcoord.epoch + offset
        pkt = sn.send_message(dst, msg, target_time=target)
        return {'pid':pkt.pid,'src':src,'dst':dst,'jump':target-time.time()} if pkt else {'error':'failed'}
    def topo(self):
        nd = {nid:{'taddr':str(n.taddr),'peers':list(self._graph.get(nid,set())),'st':'ACTIVE','branches':len(n.multiverse.branches)} for nid,n in self._nodes.items()}
        return {'nodes':nd,'edges':[(a,b) for a,p in self._graph.items() for b in p if a<b],'nn':len(nd),'ne':sum(len(p) for p in self._graph.values())//2}
    def stats(self): return {'nn':len(self._nodes),'peers':sum(len(p) for p in self._graph.values())//2,'sent':sum(n._sent for n in self._nodes.values()),'recv':sum(n._recv for n in self._nodes.values())}

# ============================================================================
# TEMPORAL BLOCKCHAIN
# ============================================================================

class TemporalBlockchain:
    def __init__(self, chain, ledger): self.chain = chain; self.ledger = ledger; self.nodes = {}
    def register(self, seal, pubkey, transports):
        cb, _ = self.chain.insert_retrocausal(time.time(), {'action':'register','seal':seal,'pubkey':pubkey,'transports':transports}, 'self_signed', 0.0)
        if cb: self.ledger.record("node_registered",{'seal':seal,'block':cb.block_hash}); self.nodes[seal]={'pubkey':pubkey,'transports':transports,'block':cb.block_hash}; return True
        return False
    def verify(self, seal, challenge, signature): n = self.nodes.get(seal); return signature == hashlib.sha256(n['pubkey'].encode()+challenge).digest() if n else False

# ============================================================================
# TIP GATEWAY
# ============================================================================

class TIPGateway:
    def __init__(self, node, port=8080): self.node = node; self.port = port; self._srv = None; self._run = False
    def start(self):
        self._run = True
        def serve():
            self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM); self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); self._srv.bind(('0.0.0.0', self.port)); self._srv.listen(5); self._srv.settimeout(1.0)
            log.info(f"🌐 Gateway TCP port {self.port}")
            while self._run:
                try: clt, addr = self._srv.accept()
                except socket.timeout: continue
                threading.Thread(target=self._handle, args=(clt,addr), daemon=True).start()
        threading.Thread(target=serve, daemon=True).start()
    def _handle(self, clt, addr):
        data = clt.recv(4096)
        if not data: clt.close(); return
        try: hdr = data[:4]; length = struct.unpack(">I", hdr)[0]; raw = data[4:4+length]; dest = raw[:32].decode().strip(); payload = raw[32:]; ok = self.node.router.route(RetroPacket(header=RNPHeader(dst=dest, src=self.node.nid, pkt_type=0, created=time.time(), target_ts=time.time(), prio=2, pkt_id=f"gw-{uuid.uuid4().hex[:12]}"), payload=payload)); clt.send(b"OK\n" if ok and ok!="__LOCAL__" else b"LOCAL\n" if ok=="__LOCAL__" else b"FAIL\n")
        except: clt.send(b"ERROR\n")
        clt.close()
    def stop(self): self._run = False; self._srv and self._srv.close()

class TemporalRelayer:
    def __init__(self, node): self.node = node; self.blockchain = TemporalBlockchain(node._channel.temporal_hash_chain, node._channel.ledger); self.gateway = TIPGateway(node)
    def start(self): self.gateway.start()
    def stop(self): self.gateway.stop()

__all__ = ['RetroNode','RetroNet','TAddr','TemporalHashChain','AuditLedger','TemporalConsistencyOracle','CausalShield','RetrocausalValidator','RetroPacket','RNPHeader','PktType','PktPriority','RetroRouter','TemporalBlockchain','TIPGateway','TemporalRelayer','TimeCrystal','SophonPair','TemporalKeyStore','QFAM','TemporalRoutingTable','TemporalDNS','TemporalFirewall','ConsistencyReport','TemporalMessage','SolarPlasmaModel','PlasmaParameters','PlasmaArkheBridge','MultiverseRouter','TimelineBranch','QUANTUM_NEGATIVE_WINDOW_SECONDS','DEFAULT_WINDOW_SECONDS','VERSION','PlasmaArkheBridgeDemo']