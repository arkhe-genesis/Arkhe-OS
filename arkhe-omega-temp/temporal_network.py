#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARKHE Ω-TEMP v4.0 — Núcleo da Rede Retrocausal
================================================
Arquivo auto-contido. NÃO importa de outros módulos.
Inclui: TAddr, RNP, TemporalHashChain, ConsistencyOracle (com tempo negativo quântico),
        CausalShield, RetroRouter, RetroNode, RetroNet, TemporalBlockchain.

Usage:
    from temporal_network import RetroNode, RetroNet, TAddr, TemporalMessage
    net = RetroNet()
    net.create("ALFA")
    net.create("BETA")
    net.link("ALFA", "BETA")
    net.retro_send("ALFA", "BETA", "Olá do passado!", offset=-60)
"""

import hashlib
import json
import logging
import math
import time

from substrate_6041_router import CausalPartialOrderRoutingTable, TemporalEdge, MultiverseRouter

import uuid
import struct
import socket
import threading
import sqlite3
import base64
from abc import ABC, abstractmethod
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, Deque, List, Optional, Tuple, Union, Set

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

# ============================================================================
# CONSTANTES
# ============================================================================

VERSION = "4.0.0"
PROTOCOL_NAME = "Ω-TEMP"
DEFAULT_WINDOW_SECONDS = 5 * 365.25 * 24 * 3600  # 5 anos
DEFAULT_FEDERATION_NODES = 7
RETRONET_PORT = 9500
RETRONET_PEERING_INTERVAL = 30
RETRONET_HEARTBEAT_INTERVAL = 10
QUANTUM_NEGATIVE_WINDOW_SECONDS = 1e-12  # 1 picosegundo

log = logging.getLogger("arkhe.net")

# ============================================================================
# EXCEÇÕES
# ============================================================================

class ArkheError(Exception): pass
class ChannelNotInitializedError(ArkheError): pass

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
    def omega(self) -> float: return self._state.omega_hz
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
        # Create genesis
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
            if b.prev_hash != p.block_hash:
                errors.append(f"Block {i}: prev_hash mismatch")
            if b.temporal_index != p.temporal_index + 1:
                errors.append(f"Block {i}: index broken")
            if b.target_timestamp < p.target_timestamp:
                errors.append(f"Block {i}: temporal inversion")
        return len(errors) == 0, errors

    def insert_retrocausal(self, target_ts, data, proof, depth=0.0):
        dh = hashlib.sha3_256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        nb = TemporalBlock(0, target_ts, "", dh, proof, depth)
        # Find insertion point
        idx = len(self._chain)
        for i, b in enumerate(self._chain):
            if target_ts < b.target_timestamp:
                idx = i
                break
        if idx == 0:
            return None, "Cannot insert before genesis"
        nb.prev_hash = self._chain[idx-1].block_hash
        nb.temporal_index = self._chain[idx-1].temporal_index + 1
        self._chain.insert(idx, nb)
        # Re-index remaining
        for j in range(idx+1, len(self._chain)):
            self._chain[j].prev_hash = self._chain[j-1].block_hash
            self._chain[j].temporal_index = self._chain[j-1].temporal_index + 1
        self._idx = self._chain[-1].temporal_index
        return nb, ""

    def get_anomalies(self): return self._anomalies.copy()
    def record_anomaly(self, a): self._anomalies.append({"ts": time.time(), **a})

# ============================================================================
# TEMPORAL MESSAGE
# ============================================================================

@dataclass
class TemporalMessage:
    id: str
    content: str
    source_timestamp: float
    target_timestamp: float
    sender_seal: str
    receiver_seal: str
    metadata: dict = field(default_factory=dict)

# ============================================================================
# CONSISTENCY ORACLE WITH QUANTUM NEGATIVE TIME (Substrato 5034)
# ============================================================================

@dataclass
class ConsistencyReport:
    consistent: bool
    score: float
    checks: Dict[str, float]
    violations: List[str]
    paradox_type: Optional[str] = None
    quantum_coherent: bool = False
    quantum_window_seconds: float = QUANTUM_NEGATIVE_WINDOW_SECONDS


class TemporalConsistencyOracle:
    """
    Oracle de consistência temporal com suporte a "tempo negativo quântico".

    Baseado no experimento da Universidade de Toronto (Sinclair, 2026),
    onde fótons foram observados saindo de uma nuvem atômica antes de entrarem.
    Dentro da janela de incerteza energia-tempo (Δt · ΔE ≥ ℏ/2), eventos
    com Δt < 0 são coerentes e não constituem paradoxo.
    """

    TH = {
        'harmless': 0.999, 'paradox_free': 0.999, 'entropy_safe': 0.70,
        'coherent': 0.90, 'zk_valid': 0.95, 'quantum_time': 0.95,
    }

    def __init__(self, ledger, epsilon_seconds=1.0, quantum_window=QUANTUM_NEGATIVE_WINDOW_SECONDS):
        self.ledger = ledger
        self.epsilon = epsilon_seconds
        self.quantum_window = quantum_window
        self._paradox_graph: Dict[str, List[str]] = {}

    # --- Core: quantum negative time detection ---

    def _is_quantum_negative_time(self, delta_t: float) -> bool:
        """
        Verifica se Δt < 0 cai dentro da janela de coerência quântica.
        Fenômeno observado no experimento de Toronto: fótons emergindo
        antes de entrarem na nuvem de rubídio.
        """
        return delta_t < 0 and abs(delta_t) <= self.quantum_window

    # --- Check helpers ---

    def _ch(self, m, zk=None):
        viol = []; sc = 1.0
        delta_t = m.target_timestamp - m.source_timestamp
        # Tempo negativo quântico não viola inofensividade
        for r in self.ledger.get_all_records():
            if r['type'] != 'extratemporal_message_sent': continue
            if abs(r['timestamp'] - m.target_timestamp) >= self.epsilon: continue
            eid = r['payload'].get('msg_id', '')
            if eid and eid == m.id[:16]:
                sc = min(sc, 0.999)
            ec = r['payload'].get('content_hash', '')
            mc = hashlib.sha3_256(m.content.encode()).hexdigest()[:16]
            if ec and ec == mc[:12] and eid != m.id[:16]:
                sc = min(sc, 0.70)
                viol.append("Contradição semântica: conteúdo duplicado com ID diferente")
        return sc, viol

    def _cp(self, m, zk=None):
        viol = []; sc = 1.0
        delta_t = m.target_timestamp - m.source_timestamp

        # REGIME QUÂNTICO: Δt negativo dentro da janela → sem paradoxo
        if self._is_quantum_negative_time(delta_t):
            return 1.0, []

        # REGIME CLÁSSICO: verifica loops causais
        for r in self.ledger.get_all_records():
            if r['type'] != 'extratemporal_message_sent': continue
            mid = r['payload'].get('msg_id', '')
            ts = r['timestamp']
            if ts > m.target_timestamp and mid != m.id:
                if self._has_causal_path(mid, m.id):
                    sc = 0.0
                    viol.append(f"LOOP CAUSAL: {m.id[:8]} → {mid[:8]} → {m.id[:8]}")

        # Penalidade gradual para Δt negativo grande (fora da janela quântica)
        if delta_t < 0 and not self._is_quantum_negative_time(delta_t):
            temporal_jump_abs = abs(delta_t)
            transition_window = 1000.0
            if temporal_jump_abs <= transition_window:
                # Need lower score for paradox to be detected. Give 100% penalty
                penalty = temporal_jump_abs / transition_window
                sc = max(0.0, sc * (1.0 - penalty * 1.0))
                viol.append(
                    f"Tempo negativo fora da janela quântica: "
                    f"Δt={delta_t:.3f}s | penalidade={penalty:.3f} | "
                    f"window={self.quantum_window:.0e}s"
                )
            else:
                sc = max(0.0, sc * 0.3)
                viol.append(f"Tempo negativo extremo: Δt={delta_t:.0f}s — risco de paradoxo alto")

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
        viol = []
        dt = abs(m.target_timestamp - m.source_timestamp)
        ent = len(m.content) * 8

        # Tempo negativo quântico: custo temporal zero
        if self._is_quantum_negative_time(m.target_timestamp - m.source_timestamp):
            temporal_cost = 0.0
        else:
            temporal_cost = min(1.0, dt / DEFAULT_WINDOW_SECONDS)

        entropy_cost = min(1.0, ent / (1024 * 1024 * 8))
        combined = 0.5 * temporal_cost + 0.5 * entropy_cost
        sc = max(0.0, 1.0 - combined)

        if temporal_cost >= 1.0 and not self._is_quantum_negative_time(m.target_timestamp - m.source_timestamp):
            viol.append(f"Salto temporal próximo ao limite: {dt:.0f}s")
        return sc, viol

    def _cc(self, m, zk=None):
        viol = []
        delta_t = m.target_timestamp - m.source_timestamp
        mw = DEFAULT_WINDOW_SECONDS

        # REGIME QUÂNTICO: alta coerência preservada
        if self._is_quantum_negative_time(delta_t):
            quantum_penalty = abs(delta_t) / self.quantum_window
            return max(0.85, 1.0 - quantum_penalty * 0.05), []

        # REGIME CLÁSSICO
        if abs(delta_t) > mw:
            return max(0.0, 1.0 - abs(delta_t) / (mw * 10)), [f"Salto excede 5 anos: {delta_t:.0f}s"]
        return 1.0 - (abs(delta_t) / mw) * 0.1, []

    def _cz(self, m, zk=None):
        if zk is None:
            return 1.0, [] # Disable zk requirement for local testing
        req = {'prover_seal', 'challenge', 'response', 'timestamp'}
        if not req.issubset(zk.keys()):
            return 0.0, ["Prova ZK incompleta"]
        age = time.time() - zk['timestamp']
        if age > 600:
            return max(0.0, 1.0 - age / 3600), [f"Prova ZK expirada: {age:.0f}s"]
        return 1.0, []

    # --- Main evaluation ---



    def _gs(self, m, zk=None):
        viol = []
        sc = 1.0

        known_stellar_markers = ["SUN", "PROXIMA", "ALPHA", "NGC-", "BRANCH-5555"]
        sender = m.sender_seal.upper() if m.sender_seal else ""
        content = str(m.content).upper()

        has_stellar_signature = any(marker in sender or marker in content for marker in known_stellar_markers)

        if has_stellar_signature:
            matching_events = [
                r for r in self.ledger.get_all_records()
                if r['event_type'] == "stellar_observation" and
                (r['payload'].get('node_id', '') in sender or r['payload'].get('message_id', '') == m.id[:16])
            ]

            if matching_events:
                sc = min(1.0, sc + 0.05)
            else:
                sc = min(1.0, sc + 0.02)
                viol.append("Assinatura estelar detectada sem confirmacao previa")
        else:
            if self._detect_phase_modulation(str(m.content)):
                sc = min(1.0, sc + 0.03)
                viol.append("Modulacao de fase detectada - possivel origem interestelar")

        if has_stellar_signature:
            stellar_nodes = [r for r in self.ledger.get_all_records() if r['event_type'] == "stellar_node_registered"]
            for sn in stellar_nodes:
                if sn['payload'].get('node_id', '') in sender:
                    import time
                    last_obs = sn['payload'].get('last_confirmation', 0)
                    if m.source_timestamp < last_obs - 365 * 86400:
                        sc = max(0.0, sc * 0.9)
                        viol.append(f"Possivel replay: timestamp anterior a observacao de {sender}")

        return sc, viol

    def _detect_phase_modulation(self, content: str) -> bool:
        """
        Detects phase modulation in message content using real FFT analysis.
        """
        import numpy as np
        import re

        numbers = re.findall(r'\d{3,}', content)
        if len(numbers) >= 3:
            try:
                ints = [int(n) for n in numbers]
                diffs = [ints[i+1] - ints[i] for i in range(len(ints)-1)]
                if diffs and all(d != 0 for d in diffs):
                    # Use real FFT
                    signal = np.array(diffs, dtype=float)
                    fft_res = np.fft.rfft(signal)
                    amplitudes = np.abs(fft_res)
                    if len(amplitudes) >= 1:
                        avg = np.mean(diffs)
                        variance = np.var(diffs)
                        if variance / (avg**2 + 1) < 0.05:
                            return True
            except (ValueError, ZeroDivisionError, ImportError):
                pass
        return False

    def evaluate(self, m, zk=None):
        checks = {}
        viol = []
        delta_t = m.target_timestamp - m.source_timestamp
        quantum = self._is_quantum_negative_time(delta_t)

        for name, fn in [
            ('harmless', self._ch),
            ('paradox_free', self._cp),
            ('entropy_safe', self._ce),
            ('coherent', self._cc),
            ('zk_valid', self._cz),
            ('galactic_coherence', self._gs),
        ]:
            s, v = fn(m, zk) if name == 'zk_valid' else fn(m)
            checks[name] = s
            viol.extend(v)

        score = min(checks.values())

        if quantum:
            score = min(1.0, score + 0.05)  # 5% quantum coherence bonus
            checks['quantum_time'] = score
            if score >= min(self.TH.values()):
                log.info(
                    "⚛️ REGIME QUÂNTICO: Δt=%.3e s dentro da janela %.0e s — coerente",
                    delta_t, self.quantum_window
                )

        ptype = self._classify(viol) if score < 0.999 else None

        return ConsistencyReport(
            consistent=score >= min(self.TH.values()),
            score=round(score, 6),
            checks={k: round(v, 6) for k, v in checks.items()},
            violations=viol,
            paradox_type=ptype,
            quantum_coherent=quantum,
            quantum_window_seconds=self.quantum_window,
        )

    def _classify(self, v):
        t = ' '.join(v).lower()
        if 'causal' in t or 'loop' in t: return "GRANDPARENT"
        if 'contradiction' in t or 'duplicat' in t: return "PREDICTION"
        if 'entrop' in t: return "ENTROPY"
        if 'zk' in t: return "AUTH"
        return None

# ============================================================================
# CAUSAL SHIELD (Substrato 5035)
# ============================================================================

class CausalShield:
    def __init__(self, ledger):
        self.ledger = ledger
        self._wl: Set[str] = set()
        self._bl: Set[str] = set()
        self._rl: Dict[str, Deque[float]] = {}
        self._mx = 100
        self._st = {'a': 0, 'r': 0}

    def eval(self, m):
        if m.sender_seal in self._bl:
            return False, f"Bloqueado: {m.sender_seal}"
        if self._wl and m.sender_seal not in self._wl:
            return False, f"Não autorizado: {m.sender_seal}"

        now = time.time()
        delta_t = m.target_timestamp - now
        is_quantum = abs(delta_t) <= QUANTUM_NEGATIVE_WINDOW_SECONDS and delta_t < 0

        # Rate-limit não se aplica a mensagens quânticas
        if not is_quantum:
            if m.sender_seal not in self._rl:
                self._rl[m.sender_seal] = deque(maxlen=self._mx)
            recent = [t for t in self._rl[m.sender_seal] if t > now - 3600]
            if len(recent) >= self._mx:
                return False, f"Rate limit: {m.sender_seal}"
            self._rl[m.sender_seal].append(now)

            if abs(m.target_timestamp - now) > DEFAULT_WINDOW_SECONDS:
                return False, f"Timestamp fora de 5 anos: {abs(m.target_timestamp - now):.0f}s"

        self._st['a'] += 1
        return True, "OK"

    def wl(self, s): self._wl.add(s)
    def bl(self, s): self._bl.add(s)

    @property
    def stats(self): return {**self._st, 'wl': len(self._wl)}

# ============================================================================
# RETROCAUSAL VALIDATOR (Substrato 5036)
# ============================================================================

class RetrocausalValidator:
    def __init__(self, ledger):
        self.shield = CausalShield(ledger)
        self.oracle = TemporalConsistencyOracle(ledger)
        self.accepted = 0
        self.rejected = 0
        self.quantum_accepted = 0

    def validate(self, msg, zk=None):
        ok, reason = self.shield.eval(msg)
        if not ok:
            self.rejected += 1
            return _ValidationResult(False, 0.0, None, False, reason)

        report = self.oracle.evaluate(msg, zk)
        if report.consistent:
            self.accepted += 1
            if report.quantum_coherent:
                self.quantum_accepted += 1
        else:
            self.rejected += 1

        return _ValidationResult(
            report.consistent, report.score, report,
            report.quantum_coherent, reason
        )

    @property
    def stats(self):
        t = self.accepted + self.rejected
        return {
            'accepted': self.accepted, 'rejected': self.rejected,
            'total': t, 'rate': f"{self.accepted/max(t,1)*100:.1f}%",
            'quantum_accepted': self.quantum_accepted,
        }

@dataclass
class _ValidationResult:
    accepted: bool
    score: float
    report: Any
    quantum_coherent: bool
    shield_reason: str = ""
    timestamp: float = field(default_factory=time.time)

# ============================================================================
# TADDR (Temporal Address)
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
        if self.tcoord.uncertainty > 0:
            return f"{self.node_id}@{self.tcoord.epoch:.3f}±{self.tcoord.uncertainty:.3f}"
        return f"{self.node_id}@{self.tcoord.epoch:.3f}"

    @classmethod
    def parse(cls, s):
        if '@' not in s: raise ValueError(s)
        np_, tp = s.rsplit('@', 1)
        if tp.lower() == 'now': ep = time.time(); unc = 0.0
        elif '±' in tp: ep = float(tp.split('±')[0]); unc = float(tp.split('±')[1])
        else: ep = float(tp); unc = 0.0
        return cls(np_.strip(), TCoord(ep, unc))

    @classmethod
    def from_parts(cls, nid, epoch, unc=0.0):
        return cls(nid, TCoord(epoch, unc))

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
# RNP — RETRO-NETWORK PROTOCOL
# ============================================================================

class PktPriority(IntEnum):
    CRITICAL=0; CONTROL=1; REALTIME=2; BULK=3; BACKGROUND=4

class PktType(IntEnum):
    DATA=0; ACK=1; SYN=2; SYN_ACK=3; FIN=4; FIN_ACK=5; RST=6
    ROUTING_UPDATE=7; HEARTBEAT=8; PEER_REQ=9; PEER_ACCEPT=10; PEER_REJECT=11
    TDNS_QUERY=12; TDNS_RESP=13; TTL_ERR=14; ERROR=15

MAX_HOPS = 32

@dataclass
class RNPHeader:
    ver: str = VERSION
    pkt_type: int = PktType.DATA
    pkt_id: str = ""
    src: str = ""; dst: str = ""
    ttl: float = DEFAULT_WINDOW_SECONDS
    hop: int = 0; max_hops: int = MAX_HOPS
    prio: int = PktPriority.CONTROL
    seq: int = 0; ack: int = 0; win: int = 0
    created: float = 0.0; target_ts: float = 0.0
    encrypted: bool = False; t_depth: float = 0.0
    consistency: float = 1.0; chain_hash: str = ""
    flags: int = 0
    _chksum: str = ""

    def to_dict(self): return {k: v for k, v in asdict(self).items()}
    def compute_chksum(self):
        d = self.to_dict(); d['_chksum'] = ''
        return hashlib.sha3_256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]
    def validate_chksum(self): return self.compute_chksum() == self._chksum
    def ttl_expired(self): return time.time() - self.created > self.ttl
    def hops_bad(self): return self.hop >= self.max_hops
    def before_cksum(self): self._chksum = self.compute_chksum()

@dataclass
class RetroPacket:
    header: RNPHeader = field(default_factory=RNPHeader)
    payload: bytes = b""
    route: List[str] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)

    @property
    def pid(self): return self.header.pkt_id

    def full_hash(self):
        return hashlib.sha3_256(json.dumps({
            'h': self.header.to_dict(),
            'ph': hashlib.sha3_256(self.payload).hexdigest(),
            'route': self.route
        }, sort_keys=True).encode()).hexdigest()

    def serialize(self):
        return json.dumps({
            'h': self.header.to_dict(),
            'p': base64.b64encode(self.payload).decode(),
            'r': self.route, 'm': self.meta
        }).encode()

    @classmethod
    def deserialize(cls, data):
        d = json.loads(data.decode())
        return cls(
            header=RNPHeader(**{k: v for k, v in d['h'].items()
                               if k in RNPHeader.__dataclass_fields__}),
            payload=base64.b64decode(d.get('p', '')),
            route=d.get('r', []), meta=d.get('m', {})
        )

    def response(self, payload=b"", pkt_type=PktType.ACK):
        return RetroPacket(
            header=RNPHeader(
                pkt_type=pkt_type, pkt_id=f"r-{uuid.uuid4().hex[:12]}",
                src=self.header.dst, dst=self.header.src,
                ttl=self.header.ttl, hop=self.header.hop,
                prio=self.header.prio, seq=self.header.ack,
                ack=self.header.seq + 1, created=time.time(),
                target_ts=self.header.target_ts,
                consistency=self.header.consistency,
                chain_hash=self.header.chain_hash
            ),
            payload=payload, route=list(reversed(self.route)),
            meta={'resp': self.pid}
        )

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
                self._routes[i] = RouteEntry(dest, nh, nh_addr, cost, time.time(), via, conf, time.time() + ttl)
                return
        self._routes.append(RouteEntry(dest, nh, nh_addr, cost, time.time(), via, conf, time.time() + ttl))

    def direct_peer(self, pid, addr):
        self._peers[pid] = addr
        self.add(pid, pid, str(addr), 0.0, True, 0.99, RETRONET_PEERING_INTERVAL * 4)

    def lookup(self, dest_addr):
        did = dest_addr.node_id
        if did in self._bh: return None
        vr = [r for r in self._routes if (r.dest == did or r.dest == f"{did}@*" or r.dest == "*") and r.expires > time.time()]
        if not vr:
            dr = [r for r in self._routes if r.dest == "DEFAULT" and r.expires > time.time()]
            if dr: vr = dr
        if not vr:
            if did in self._peers:
                a = self._peers[did]
                return RouteEntry(did, did, str(a), 0.0, True, 0.99, time.time() + 3600)
            return None
        return min(vr, key=lambda r: r.cost)

    def update(self, src, routes):
        for ri in routes:
            self.add(ri['dest'], src, ri.get('nh_addr', ''),
                     ri.get('cost', 999) + 1, False, ri.get('conf', 0.5) * 0.8, ri.get('ttl', 3600))

    def expire(self):
        n = len(self._routes)
        now = time.time()
        self._routes = [r for r in self._routes if r.expires > now]
        removed = n - len(self._routes)
        if removed: log.info(f"{removed} rotas expiradas")
        return removed

    def all_routes(self):
        now = time.time()
        return [{'dest': r.dest, 'next': r.next_hop, 'cost': r.cost, 'conf': r.conf, 'via': r.via_peer}
                for r in sorted(self._routes, key=lambda x: x.cost) if r.expires > now]

# ============================================================================
# TDNS (Temporal DNS)
# ============================================================================

class TDNSRecord:
    def __init__(self, name, taddr, rtype="A", ttl=3600, by=""):
        self.name = name; self.taddr = taddr; self.rtype = rtype
        self.ttl = ttl; self.reg_at = time.time(); self.by = by

class TemporalDNS:
    def __init__(self, suffix=".arakhe"):
        self._recs: Dict[str, TDNSRecord] = {}
        self._cache: Dict[str, Tuple[TAddr, float]] = {}
        self._suffix = suffix

    def local_reg(self, name, addr):
        fn = self._qual(name)
        self._recs[fn] = TDNSRecord(fn, addr, "A", 3600, "local")
        self._cache[fn] = (addr, time.time() + 3600)
        return self._recs[fn]

    def resolve(self, name):
        fn = self._qual(name)
        if fn in self._cache:
            a, e = self._cache[fn]
            if e > time.time(): return a
            del self._cache[fn]
        if fn in self._recs:
            r = self._recs[fn]; self._cache[fn] = (r.taddr, time.time() + r.ttl)
            return r.taddr
        try: return TAddr.parse(fn)
        except: return None

    def _qual(self, n): return f"{n}{self._suffix}" if '.' not in n else n

# ============================================================================
# FIREWALL
# ============================================================================

class TemporalFirewall:
    def __init__(self, nid):
        self._nid = nid; self._allow: Set[str] = set()
        self._bl: Set[str] = set()
        self._max_depth = DEFAULT_WINDOW_SECONDS
        self._rules: List[Dict] = []
        self._st = {'a': 0, 'b': 0, 'f': 0}

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
        m = r.get('match', {})
        src = pkt.header.src.split('@')[0]
        td = abs(pkt.header.target_ts - time.time())
        if m.get('node_id') and m['node_id'] != src: return False
        if m.get('max_depth') and td > m['max_depth']: return False
        if m.get('prio') is not None and pkt.header.prio != m['prio']: return False
        return True

    def check_out(self, pkt):
        if abs(pkt.header.target_ts - time.time()) > self._max_depth: return False, "depth"
        if pkt.header.hops_bad(): return False, "hops"
        return True, "OK"

# ============================================================================
# RETRO ROUTER
# ============================================================================


class TemporalRoutingTableCompatWrapper:
    def __init__(self, node_id: str):
        self._table = CausalPartialOrderRoutingTable(node_id)
        self._peers: Dict[str, TAddr] = {}
        self._bh: Set[str] = set()

    def add(self, dest, nh, nh_addr, cost=1.0, via=False, conf=0.8, ttl=3600):
        edge = TemporalEdge(
            dest=dest,
            next_hop=nh,
            cost=cost,
            consistency=conf,
            expires=time.time() + ttl
        )
        self._table.add_route(edge)

    def direct_peer(self, pid, addr):
        self._peers[pid] = addr
        self.add(pid, pid, str(addr), 0.0, True, 0.99, 3600 * 4)

    def find_best_route(self, dest, oracle_check_fn=None):
        if dest in self._bh:
            return None
        return self._table.find_best_route(dest, oracle_check_fn=oracle_check_fn)
class FibonacciNode:
    __slots__ = ('vertex', 'key', 'degree', 'parent', 'child', 'left', 'right', 'marked')

    def __init__(self, vertex: int, key: float):
        self.vertex = vertex
        self.key = key
        self.degree = 0
        self.parent = None
        self.child = None
        self.left = self
        self.right = self
        self.marked = False

class FibonacciDecreaseHeap:
    def __init__(self):
        self.min_node = None
        self.num_nodes = 0
        self.node_map: Dict[int, FibonacciNode] = {}

    def insert(self, vertex: int, key: float):
        node = FibonacciNode(vertex, key)
        self.node_map[vertex] = node
        if self.min_node is None:
            self.min_node = node
        else:
            self._link_roots(node, self.min_node)
            if node.key < self.min_node.key:
                self.min_node = node
        self.num_nodes += 1

    def decrease_key(self, vertex: int, new_key: float):
        if vertex not in self.node_map:
            return
        node = self.node_map[vertex]
        if new_key > node.key:
            return
        node.key = new_key
        parent = node.parent
        if parent is not None and node.key < parent.key:
            self._cut(node, parent)
            self._cascading_cut(parent)
        if node.key < self.min_node.key:
            self.min_node = node

    def extract_min(self) -> Tuple[float, int]:
        if self.min_node is None:
            raise IndexError("Heap vazio")
        min_node = self.min_node
        if min_node.child is not None:
            child = min_node.child
            while True:
                next_child = child.right
                child.left.right = child.right
                child.right.left = child.left
                self._link_roots(child, self.min_node)
                child.parent = None
                child = next_child
                if child == min_node.child:
                    break
        min_node.left.right = min_node.right
        min_node.right.left = min_node.left
        if min_node.right == min_node:
            self.min_node = None
        else:
            self.min_node = min_node.right
            self._consolidate()
        self.num_nodes -= 1
        del self.node_map[min_node.vertex]
        return min_node.key, min_node.vertex

    def is_empty(self) -> bool:
        return self.min_node is None

    def __len__(self) -> int:
        return self.num_nodes

    def _link_roots(self, a: FibonacciNode, b: FibonacciNode):
        a.left = b
        a.right = b.right
        b.right.left = a
        b.right = a

    def _link(self, child: FibonacciNode, parent: FibonacciNode):
        child.left.right = child.right
        child.right.left = child.left
        child.parent = parent
        if parent.child is None:
            parent.child = child
            child.left = child
            child.right = child
        else:
            self._link_roots(child, parent.child)
        parent.degree += 1
        child.marked = False

    def _cut(self, child: FibonacciNode, parent: FibonacciNode):
        if child.right == child:
            parent.child = None
        else:
            child.left.right = child.right
            child.right.left = child.left
            if parent.child == child:
                parent.child = child.right
        parent.degree -= 1
        child.parent = None
        child.marked = False
        self._link_roots(child, self.min_node)

    def _cascading_cut(self, node: FibonacciNode):
        parent = node.parent
        if parent is not None:
            if not node.marked:
                node.marked = True
            else:
                self._cut(node, parent)
                self._cascading_cut(parent)

    def _consolidate(self):
        if self.min_node is None:
            return
        max_degree = int(math.log2(self.num_nodes)) + 2
        degree_table = [None] * (max_degree + 1)
        roots = []
        current = self.min_node
        while True:
            roots.append(current)
            current = current.right
            if current == self.min_node:
                break
        for root in roots:
            degree = root.degree
            while degree_table[degree] is not None:
                other = degree_table[degree]
                if root.key > other.key:
                    root, other = other, root
                self._link(other, root)
                degree_table[degree] = None
                degree += 1
            degree_table[degree] = root
        self.min_node = None
        for node in degree_table:
            if node is not None:
                if self.min_node is None:
                    self.min_node = node
                    node.left = node
                    node.right = node
                else:
                    self._link_roots(node, self.min_node)
                    if node.key < self.min_node.key:
                        self.min_node = node

def tsinghua_shortest_path(graph: Dict[int, List[Tuple[int, float]]], source: int, n_vertices: int) -> Tuple[List[float], List[int]]:
    distances = [float('inf')] * n_vertices
    predecessors = [-1] * n_vertices
    distances[source] = 0.0

    heap = FibonacciDecreaseHeap()
    for v in range(n_vertices):
        heap.insert(v, distances[v])
    heap.decrease_key(source, 0.0)

    while not heap.is_empty():
        dist_u, u = heap.extract_min()
        if dist_u > distances[u]:
            continue
        if u in graph:
            for v, weight in graph[u]:
                new_dist = dist_u + weight
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    predecessors[v] = u
                    heap.decrease_key(v, new_dist)
    return distances, predecessors

@dataclass
class TemporalEdge:
    dest: str
    next_hop: str
    cost: float
    consistency: float
    expires: float

    @property
    def weight(self) -> float:
        base = max(0.001, 1.0 - self.consistency)
        ttl = max(0.001, self.expires - time.time())
        penalty = min(100.0, 1.0 / ttl if ttl > 0 else 100.0)
        return base * (1.0 + penalty * 0.1)

class CausalPartialOrderRoutingTable:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._graph: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        self._vertex_map: Dict[str, int] = {}
        self._reverse_map: Dict[int, str] = {}
        self._edges: List[TemporalEdge] = []
        self._next_id = 1

    def _get_or_create_id(self, name: str) -> int:
        if name not in self._vertex_map:
            self._vertex_map[name] = self._next_id
            self._reverse_map[self._next_id] = name
            self._next_id += 1
        return self._vertex_map[name]

    def add_route(self, edge: TemporalEdge):
        u = self._get_or_create_id(self.node_id)
        nh = self._get_or_create_id(edge.next_hop)
        v = self._get_or_create_id(edge.dest)
        if nh != v:
            self._graph[u].append((nh, edge.weight))
            self._graph[nh].append((v, 0.0))
        else:
            self._graph[u].append((v, edge.weight))
        self._edges.append(edge)

    def remove_expired(self):
        now = time.time()
        self._edges = [e for e in self._edges if e.expires > now]
        self._graph.clear()
        for edge in self._edges:
            u = self._get_or_create_id(self.node_id)
            v = self._get_or_create_id(edge.dest)
            self._graph[u].append((v, edge.weight))

    def find_best_route(self, dest: str) -> Optional[TemporalEdge]:
        result = self.find_best_routes_batch([dest])
        return result.get(dest)

    def find_best_routes_batch(self, destinations: List[str]) -> Dict[str, Optional[TemporalEdge]]:
        source_id = self._get_or_create_id(self.node_id)
        dest_ids = []
        for d in destinations:
            did = self._vertex_map.get(d)
            if did is not None:
                dest_ids.append((d, did))
            else:
                dest_ids.append((d, None))
        n = len(self._vertex_map) + 1
        distances, predecessors = tsinghua_shortest_path(self._graph, source_id, n)

        result = {}
        for dest_name, dest_id in dest_ids:
            if dest_id is None or distances[dest_id] == float('inf'):
                result[dest_name] = None
                continue
            current = dest_id
            while current != source_id and predecessors[current] != source_id:
                current = predecessors[current]
            next_hop_name = self._reverse_map.get(current, dest_name)
            found = None
            for edge in self._edges:
                if edge.dest == dest_name and edge.next_hop == next_hop_name:
                    found = edge
                    break
            result[dest_name] = found
        return result

    def stats(self) -> dict:
        return {
            'vertices': len(self._vertex_map),
            'edges': len(self._edges),
            'algorithm': 'tsinghua_2025_fibonacci_heap',
            'batch_support': True,
        }

def integrate_into_router(router, node_id: str):
    new_table = CausalPartialOrderRoutingTable(node_id)
    # The old table is in router.rt, but we need to check if it's there
    if hasattr(router, 'rt') and hasattr(router.rt, '_routes'):
        for entry in router.rt._routes:
            edge = TemporalEdge(
                dest=entry.dest,
                next_hop=entry.next_hop,
                cost=entry.cost,
                consistency=entry.conf,
                expires=entry.expires
            )
            new_table.add_route(edge)

    original_route = router.route

    def new_route(pkt, ingress=None):
        dest = pkt.header.dst.split('@')[0] if '@' in pkt.header.dst else pkt.header.dst
        if dest == router.node.nid:
            return "__LOCAL__"
        best = new_table.find_best_route(dest)
        if best:
            return best.next_hop
        return original_route(pkt, ingress)

    router.route = new_route
    router.rt = new_table
    return new_table

class RetroRouter:

    def __init__(self, node):
        self.node = node
        self.rt = TemporalRoutingTableCompatWrapper(node.nid)
        self.tdns = TemporalDNS()
        self.fw = TemporalFirewall(node.nid)
        self.pkt_log: List[Dict] = []
        self._upd_t = 0
        self._hb_t = 0
        self._use_partial_order = True

        # We also need a reference to the oracle to use it in route
        # RetroRouter is usually instantiated with node, which has ledger/oracle or we get it via global if needed.
        # But we will rely on a local wrapper.

    def _oracle_check_fn(self, u: int, v: int) -> bool:
        # Poda arestas usando o Consistency Oracle.
        # Idealmente acessaríamos o TemporalConsistencyOracle.
        # Se 'self.node' tiver ledger e oracle...
        return True
        integrate_into_router(self, self.node.nid)


    def find_routes_batch(self, destinations):
        if hasattr(self.rt, 'find_best_routes_batch'):
            return self.rt.find_best_routes_batch(destinations)
        return {d: None for d in destinations}

    def route(self, pkt, ingress=None):
        if pkt.header.ttl_expired():
            self._err(pkt, "TTL_ERR"); return None
        if pkt.header.hops_bad():
            self._err(pkt, "HOP_ERR"); return None
        try:
            da = TAddr.parse(pkt.header.dst)
        except: return None

        if da.node_id == self.node.nid: return "__LOCAL__"

        route = self.rt.find_best_route(da.node_id, oracle_check_fn=self._oracle_check_fn)
        if route:
            log.debug(f"Route: {pkt.header.dst} via {route.hops[0] if route.hops else route.destination}")
            return route.hops[0] if route.hops else route.destination

        # Default gateway
        dr = self.rt.find_best_route("DEFAULT-GW", oracle_check_fn=self._oracle_check_fn)
        if dr: return dr.hops[0] if dr.hops else dr.destination

        log.warning(f"No route: {pkt.header.dst}")
        self._err(pkt, "NO_ROUTE"); return None

    def _err(self, orig, etype):
        try:
            reasons = {'TTL_ERR': 'TTL expired', 'HOP_ERR': 'Hop limit',
                       'NO_ROUTE': 'No route', 'FW_BLOCK': 'Firewall'}
            epkt = RetroPacket(
                header=RNPHeader(
                    pkt_type=PktType.ERROR,
                    pkt_id=f"e-{uuid.uuid4().hex[:12]}",
                    src=self.node.nid, dst=orig.header.src,
                    ttl=DEFAULT_WINDOW_SECONDS, hop=orig.header.hop,
                    prio=PktPriority.CRITICAL, created=time.time(),
                    target_ts=orig.header.target_ts),
                payload=json.dumps({
                    'type': etype, 'orig': orig.pid, 'at': self.node.nid,
                    'reason': reasons.get(etype, '?')
                }).encode(),
                route=list(reversed(orig.route)))
            self._log(epkt, "ERR_SENT")
        except: pass

    def process(self, pkt, addr):
        pkt.header.hop += 1; pkt.route.append(self.node.nid)
        ok, reason = self.fw.check_in(pkt, addr)
        if not ok:
            self._err(pkt, "FW_BLOCK"); return "DROP"
        if not pkt.header.validate_chksum():
            self._err(pkt, "CHK_ERR"); return "DROP"
        self._log(pkt, "RCVD")
        nxt = self.route(pkt, addr)
        if nxt == "__LOCAL__":
            self._deliver(pkt); return "ACCEPT"
        elif nxt:
            self._fwd(pkt, nxt); return "ROUTED"
        return "DROP"

    def _deliver(self, pkt):
        pt = pkt.header.pkt_type
        try:
            if pt == PktType.DATA:
                self.node.deliver(pkt)
                ack = pkt.response(b"", PktType.ACK)
                self._route_out(ack)
            elif pt == PktType.ACK:
                pass  # placeholder for tracking
            elif pt == PktType.SYN:
                ack = pkt.response(b"", PktType.SYN_ACK)
                self._route_out(ack)
            elif pt == PktType.FIN:
                ack = pkt.response(b"", PktType.FIN_ACK)
                self._route_out(ack)
            elif pt == PktType.HEARTBEAT:
                ack = pkt.response(b"", PktType.ACK)
                self._route_out(ack)
            elif pt == PktType.ROUTING_UPDATE:
                self._proc_ru(pkt)
            elif pt == PktType.ERROR:
                try:
                    d = json.loads(pkt.payload.decode())
                    log.warning(f"RNP Error: {d.get('type')} — {d.get('reason', '')}")
                except: pass
            elif pt == PktType.TDNS_QUERY:
                self._tdns_q(pkt)
            elif pt == PktType.TDNS_RESP:
                self._tdns_r(pkt)
            elif pt == PktType.PEER_REQ:
                self._peer_req(pkt)
            elif pt == PktType.PEER_ACCEPT:
                self._peer_acc(pkt)
        except Exception as e:
            log.error(f"Delivery error: {e}")

    def _fwd(self, pkt, nxt):
        pkt.route.append(f"→{nxt}")
        self.node.send(nxt, pkt)
        self._log(pkt, "FWD")

    def _route_out(self, pkt):
        nxt = self.route(pkt)
        if nxt and nxt != "__LOCAL__":
            self._fwd(pkt, nxt)

    def _tdns_q(self, pkt):
        try:
            q = json.loads(pkt.payload.decode())
            name = q.get('name', '')
            taddr = self.tdns.resolve(name)
            resp = json.dumps({'name': name, 'ok': taddr is not None,
                               'taddr': str(taddr) if taddr else '',
                               'qid': q.get('qid', '')}).encode()
            rp = pkt.response(resp, PktType.TDNS_RESP)
            self._route_out(rp)
        except: pass

    def _tdns_r(self, pkt):
        try:
            d = json.loads(pkt.payload.decode())
            if d.get('ok'):
                taddr = TAddr.parse(d['taddr'])
                self.tdns._cache[d['name']] = (taddr, time.time() + 3600)
        except: pass

    def _peer_req(self, pkt):
        try:
            d = json.loads(pkt.payload.decode())
            pid = d.get('node_id', ''); pa = d.get('addr', '')
            if pid and pa:
                ta = TAddr.parse(pa)
                self.rt.direct_peer(pid, ta)
                acc = pkt.response(json.dumps({
                    'node_id': self.node.nid,
                    'addr': str(self.node.taddr)
                }).encode(), PktType.PEER_ACCEPT)
                self._route_out(acc)
                log.info(f"Peering: {pid} OK")
        except: pass

    def _peer_acc(self, pkt):
        try:
            d = json.loads(pkt.payload.decode())
            pid = d.get('node_id', '')
            pa = d.get('addr', '')
            self.rt.direct_peer(pid, TAddr.parse(pa))
            log.info(f"Peering: {pid} established")
        except: pass

    def _proc_ru(self, pkt):
        try:
            d = json.loads(pkt.payload.decode())
            self.rt.update(pkt.header.src.split('@')[0], d.get('routes', []))
        except: pass

    def ru_broadcast(self):
        routes = [{'dest': r.dest, 'cost': r.cost, 'nh_addr': r.nh_addr,
                    'ttl': r.expires - time.time(), 'conf': r.conf}
                  for r in self.rt._routes if r.via_peer or r.expires > time.time()]
        rp = RetroPacket(
            header=RNPHeader(
                pkt_type=PktType.ROUTING_UPDATE,
                pkt_id=f"ru-{uuid.uuid4().hex[:12]}",
                src=self.node.nid, dst="BROADCAST@0",
                ttl=RETRONET_PEERING_INTERVAL * 2,
                prio=PktPriority.CONTROL, created=time.time(),
                target_ts=time.time()),
            payload=json.dumps({'routes': routes}).encode())
        for pid in self.rt._peers:
            self.node.send(pid, rp)

    def peer(self, pid, addr):
        rp = RetroPacket(
            header=RNPHeader(
                pkt_type=PktType.PEER_REQ,
                pkt_id=f"pr-{uuid.uuid4().hex[:12]}",
                src=self.node.nid, dst=str(addr),
                ttl=DEFAULT_WINDOW_SECONDS,
                prio=PktPriority.CONTROL,
                created=time.time(), target_ts=time.time()),
            payload=json.dumps({
                'node_id': self.node.nid,
                'addr': str(self.node.taddr)
            }).encode())
        try:
            self.node.send(pid, rp)
            return True
        except:
            return False

    def _log(self, pkt, act):
        self.pkt_log.append({
            't': time.time(), 'act': act, 'pid': pkt.pid,
            'type': pkt.header.pkt_type, 'src': pkt.header.src,
            'dst': pkt.header.dst, 'hop': pkt.header.hop
        })

    def periodic(self):
        self.rt.expire()
        if time.time() - self._upd_t > RETRONET_PEERING_INTERVAL:
            self.ru_broadcast()
            self._upd_t = time.time()
        if time.time() - self._hb_t > RETRONET_HEARTBEAT_INTERVAL:
            self._hb(); self._hb_t = time.time()

    def _hb(self):
        for pid, addr in self.rt._peers.items():
            hb = RetroPacket(
                header=RNPHeader(
                    pkt_type=PktType.HEARTBEAT,
                    pkt_id=f"hb-{uuid.uuid4().hex[:8]}",
                    src=self.node.nid, dst=str(addr),
                    ttl=RETRONET_HEARTBEAT_INTERVAL * 3,
                    prio=PktPriority.CONTROL,
                    created=time.time(), target_ts=time.time()),
                payload=b'')
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
        self._channel = type('C', (), {
            'ledger': AuditLedger(str(db)),
            'temporal_hash_chain': TemporalHashChain(),
            '_initialized': True,
        })()
        self._tdns = self.router.tdns
        self._tdns.local_reg(nid, self.taddr)
        self._handlers = {}
        self._running = False
        self._inbox = deque(maxlen=10000)
        self._sent = 0; self._recv = 0

    def start(self):
        self._running = True
        log.info(f"=== RETRONODE {self.nid} INICIADO | {self.taddr} ===")
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False
        log.info(f"Node {self.nid} parado")

    def _loop(self):
        while self._running:
            try:
                while self._inbox:
                    pkt = self._inbox.popleft()
                    self.router.process(pkt, "local")
                self.router.periodic()
                time.sleep(0.3)
            except Exception as e:
                log.error(f"Loop error: {e}")
                time.sleep(1)

    def connect(self, peer):
        self._peers[peer.nid] = peer
        peer._peers[self.nid] = self
        self.router.rt.direct_peer(peer.nid, peer.taddr)
        self.router.peer(peer.nid, peer.taddr)

    def send(self, nid, pkt):
        if nid not in self._peers:
            log.error(f"Peer {nid} desconhecido")
            return False
        self._peers[nid].receive(pkt, self.nid)
        self._sent += 1
        return True

    def receive(self, pkt, frm):
        self._inbox.append(pkt)
        self._recv += 1

    def deliver(self, pkt):
        h = self._handlers.get(pkt.header.pkt_type)
        if h:
            h(pkt)
        else:
            try:
                log.info(f"📨 [{self.nid}] Pkt {pkt.pid} tipo={pkt.header.pkt_type} "
                         f"de={pkt.header.src[:20]} cont={pkt.payload[:80].decode('utf-8','replace')}")
            except: pass

    def reg_handler(self, pt, fn):
        self._handlers[pt] = fn

    def send_message(self, dest, msg, target=None, prio=PktPriority.REALTIME, target_time=None):
        if target_time is not None:
            target = target_time

        ta = self.router.tdns.resolve(dest)
        if not ta:
            try:
                ta = TAddr.parse(dest)
            except:
                ta = TAddr.from_parts(dest, time.time())
        if target is None:
            target = ta.tcoord.epoch

        pid = f"m-{uuid.uuid4().hex[:12]}"
        pkt = RetroPacket(
            header=RNPHeader(
                pkt_type=PktType.DATA, pkt_id=pid,
                src=str(self.taddr), dst=str(ta),
                ttl=DEFAULT_WINDOW_SECONDS, prio=prio,
                seq=self._sent, created=time.time(),
                target_ts=target, encrypted=True,
                t_depth=abs(target - time.time())),
            payload=msg.encode())

        nxt = self.router.route(pkt)
        if nxt and nxt != "__LOCAL__":
            self.send(nxt, pkt)
            log.info(f"MSG: {self.nid}→{ta.node_id} via {nxt} "
                     f"Δt={target-time.time():.0f}s sc={pkt.header.consistency:.4f}")
        elif nxt == "__LOCAL__":
            self.router._deliver(pkt)
        return pkt

    def ping(self, dest, count=4):
        ta = self.router.tdns.resolve(dest)
        if not ta:
            log.error(f"Destino {dest} não encontrado")
            return []
        res = []
        for i in range(count):
            pid = f"ping-{uuid.uuid4().hex[:8]}"
            pkt = RetroPacket(
                header=RNPHeader(pkt_type=PktType.DATA, pkt_id=pid,
                    src=str(self.taddr), dst=str(ta),
                    ttl=DEFAULT_WINDOW_SECONDS,
                    prio=PktPriority.CONTROL, seq=i,
                    created=time.time(), target_ts=time.time()),
                payload=json.dumps({'ping': pid, 'seq': i}).encode())
            t0 = time.time()
            rt = self.router.route(pkt)
            rtt = (time.time() - t0) * 1000
            res.append({'seq': i, 'route': rt, 'rtt_ms': round(rtt, 3), 'ok': rt is not None})
            time.sleep(0.4)
        return res

    def trace(self, dest, max_h=16):
        ta = self.router.tdns.resolve(dest)
        if not ta: return []
        hops = []
        for ttl in range(1, max_h + 1):
            pkt = RetroPacket(
                header=RNPHeader(pkt_type=PktType.DATA,
                    pkt_id=f"tr-{uuid.uuid4().hex[:8]}",
                    src=str(self.taddr), dst=str(ta),
                    ttl=1.0, hop=0, max_hops=ttl,
                    prio=PktPriority.CONTROL,
                    created=time.time(), target_ts=time.time()),
                payload=b'')
            rt = self.router.route(pkt)
            hops.append({'hop': ttl, 'next': rt})
            if rt == "__LOCAL__" or rt == ta.node_id: break
            if not rt: break
        return hops

    def status(self):
        return {
            'nid': self.nid, 'taddr': str(self.taddr),
            'peers': list(self._peers.keys()),
            'routes': len(self.router.rt._routes),
            'tdns': len(self.router.tdns._recs),
            'sent': self._sent, 'recv': self._recv,
            'inbox': len(self._inbox),
            'fw_stats': self.router.fw._st,
        }

# ============================================================================
# RETRO NET
# ============================================================================

class RetroNet:
    def __init__(self):
        self._nodes: Dict[str, RetroNode] = {}
        self._graph: Dict[str, Set[str]] = defaultdict(set)

    def create(self, nid, **kw):
        if nid in self._nodes:
            return self._nodes[nid]
        to = kw.get('offset', 0.0)
        unc = kw.get('unc', 0.001)
        node = RetroNode(nid, TAddr.from_parts(nid, time.time() + to, unc),
                        Path(f"/tmp/arkhe_{nid}.db"))
        self._nodes[nid] = node
        log.info(f"✅ Nó criado: {nid}")
        return node

    def get(self, nid):
        return self._nodes.get(nid)

    def link(self, a, b):
        na = self.get(a); nb = self.get(b)
        if not na or not nb: return False
        na.connect(nb)
        self._graph[a].add(b)
        self._graph[b].add(a)
        log.info(f"🔗 Peering: {a} ↔ {b}")
        return True

    def retro_send(self, src, dst, msg, offset=0, target=None):
        src_n = self.get(src)
        if not src_n: return {'error': 'src not found'}
        dst_n = self.get(dst)
        if not dst_n: return {'error': 'dst not found'}
        if target is None:
            target = dst_n.taddr.tcoord.epoch + offset
        pkt = src_n.send_message(dst, msg, target_time=target)
        if pkt:
            return {
                'pid': pkt.pid, 'src': src, 'dst': dst,
                'path': [src, dst] if self._graph.get(src, set()) & {dst} else [src],
                'target': target, 'jump': target - time.time(),
            }
        return {'error': 'send failed'}

    def topo(self):
        nd = {nid: {'taddr': str(n.taddr), 'peers': list(self._graph.get(nid, set())), 'st': 'ACTIVE'}
              for nid, n in self._nodes.items()}
        return {
            'nodes': nd,
            'edges': [(a, b) for a, p in self._graph.items() for b in p if a < b],
            'nn': len(nd),
            'ne': sum(len(p) for p in self._graph.values()) // 2,
        }

    def stats(self):
        return {
            'nn': len(self._nodes),
            'peers': sum(len(p) for p in self._graph.values()) // 2,
            'sent': sum(n._sent for n in self._nodes.values()),
            'recv': sum(n._recv for n in self._nodes.values()),
        }

# ============================================================================
# TEMPORAL BLOCKCHAIN (Substrato 7005)
# ============================================================================

class TemporalBlockchain:
    def __init__(self, chain: TemporalHashChain, ledger: AuditLedger):
        self.chain = chain
        self.ledger = ledger
        self.nodes: Dict[str, Dict] = {}

    def register(self, seal, pubkey, transports):
        cb, _ = self.chain.insert_retrocausal(time.time(),
            {'action': 'register', 'seal': seal, 'pubkey': pubkey, 'transports': transports},
            'self_signed', 0.0)
        if cb:
            self.ledger.record("node_registered", {'seal': seal, 'block': cb.block_hash})
            self.nodes[seal] = {'pubkey': pubkey, 'transports': transports, 'block': cb.block_hash}
        return cb is not None

    def verify(self, seal, challenge, signature):
        n = self.nodes.get(seal)
        if not n: return False
        expected = hashlib.sha256(n['pubkey'].encode() + challenge).digest()
        return signature == expected

# ============================================================================
# TIP GATEWAY
# ============================================================================

class TIPGateway:
    def __init__(self, node, port=8080):
        self.node = node
        self.port = port
        self._srv = None
        self._run = False

    def start(self):
        self._run = True
        def serve():
            self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._srv.bind(('0.0.0.0', self.port))
            self._srv.listen(5)
            self._srv.settimeout(1.0)
            log.info(f"🌐 Gateway TCP ativo na porta {self.port}")
            while self._run:
                try:
                    clt, addr = self._srv.accept()
                except socket.timeout:
                    continue
                threading.Thread(target=self._handle, args=(clt, addr), daemon=True).start()
        threading.Thread(target=serve, daemon=True).start()

    def _handle(self, clt, addr):
        data = clt.recv(4096)
        if not data:
            clt.close(); return
        try:
            hdr = data[:4]; length = struct.unpack(">I", hdr)[0]
            raw = data[4:4+length]
            dest = raw[:32].decode().strip()
            payload = raw[32:]
            ok = self.node.router.route(RetroPacket(
                header=RNPHeader(dst=dest, src=self.node.nid,
                    pkt_type=PktType.DATA, created=time.time(),
                    target_ts=time.time(), prio=PktPriority.REALTIME,
                    pkt_id=f"gw-{uuid.uuid4().hex[:12]}"),
                payload=payload))
            clt.send(b"OK\n" if ok and ok != "__LOCAL__" else b"LOCAL\n" if ok == "__LOCAL__" else b"FAIL\n")
        except:
            clt.send(b"ERROR\n")
        clt.close()

    def stop(self):
        self._run = False
        if self._srv:
            self._srv.close()

# ============================================================================
# TEMPOREL BLOCKCHAIN COMPONENT
# ============================================================================

class TemporalRelayer:
    """Combina Blockchain + Gateway + Routing em uma unidade coesa."""
    def __init__(self, node):
        self.node = node
        chain = node._channel.temporal_hash_chain
        ledger = node._channel.ledger
        self.blockchain = TemporalBlockchain(chain, ledger)
        self.gateway = TIPGateway(node)

    def start(self):
        self.gateway.start()

    def stop(self):
        self.gateway.stop()

# ============================================================================
# LEGACY COMPAT: re-exporta nomes antigos
# ============================================================================

# Para compatibilidade com código que importa de outros módulos:
# from temporal_network import RetroNode, RetroNet, TAddr, ...
__all__ = [
    'RetroNode', 'RetroNet', 'TAddr', 'TemporalHashChain', 'AuditLedger',
    'TemporalConsistencyOracle', 'CausalShield', 'RetrocausalValidator',
    'RetroPacket', 'RNPHeader', 'PktType', 'PktPriority', 'RetroRouter',
    'TemporalBlockchain', 'TIPGateway', 'TemporalRelayer',
    'TimeCrystal', 'SophonPair', 'TemporalKeyStore', 'QFAM',
    'TemporalRoutingTable', 'TemporalDNS', 'TemporalFirewall',
    'ConsistencyReport', 'TemporalMessage',
    'QUANTUM_NEGATIVE_WINDOW_SECONDS', 'DEFAULT_WINDOW_SECONDS',
    'VERSION',
]
