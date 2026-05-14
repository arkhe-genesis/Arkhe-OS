import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum, auto

# ===== SUBSTRATO 5033: TemporalHashChain =====

@dataclass
class TemporalBlock:
    block_id: str
    prev_hash: str
    timestamp_ns: int
    payload_hash: str
    payload_type: str
    metadata: Dict
    merkle_root: str
    signature: Optional[str] = None
    coherence_proof: Optional[str] = None

class TemporalHashChain:
    def __init__(self):
        self.blocks: List[TemporalBlock] = []
        self._genesis()

    def _genesis(self):
        genesis = TemporalBlock(
            block_id="0" * 64,
            prev_hash="0" * 64,
            timestamp_ns=0,
            payload_hash="0" * 64,
            payload_type="genesis",
            metadata={"version": "5.1.0"},
            merkle_root="0" * 64,
        )
        self.blocks.append(genesis)

    def _hash(self, data: str) -> str:
        return hashlib.sha3_256(data.encode()).hexdigest()

    def anchor(self, payload: str, payload_type: str, metadata: Dict,
               signature: Optional[str] = None, coherence_proof: Optional[str] = None) -> TemporalBlock:
        prev = self.blocks[-1]
        ts_ns = int(time.time() * 1e9)
        payload_hash = self._hash(payload)
        header = f"{prev.block_id}:{ts_ns}:{payload_hash}:{payload_type}"
        block_id = self._hash(header)
        merkle_root = self._hash(f"{block_id}:{payload_hash}")
        block = TemporalBlock(
            block_id=block_id,
            prev_hash=prev.block_id,
            timestamp_ns=ts_ns,
            payload_hash=payload_hash,
            payload_type=payload_type,
            metadata=metadata,
            merkle_root=merkle_root,
            signature=signature,
            coherence_proof=coherence_proof,
        )
        self.blocks.append(block)
        return block

    def verify_chain(self) -> bool:
        for i in range(1, len(self.blocks)):
            curr = self.blocks[i]
            prev = self.blocks[i-1]
            if curr.prev_hash != prev.block_id:
                return False
            header = f"{prev.block_id}:{curr.timestamp_ns}:{curr.payload_hash}:{curr.payload_type}"
            if self._hash(header) != curr.block_id:
                return False
        return True

    def get_latest(self) -> TemporalBlock:
        return self.blocks[-1]

# ===== SUBSTRATO 5034: ConsistencyOracle v4.3.0 =====

class ConsistencyReport:
    def __init__(self):
        self.consistent: bool = False
        self.score: float = 0.0
        self.checks: Dict[str, float] = {}
        self.violations: List[str] = []
        self.paradox_type: Optional[str] = None
        self.quantum_coherent: bool = False
        self.quantum_window_seconds: float = 0.0
        self.solar_coherent: bool = False
        self.galactic_coherent: bool = False
        self.observer_distance_au: float = 0.0

class ConsistencyOracle:
    THRESHOLDS = {
        "harmless": 0.999,
        "paradox_free": 0.999,
        "entropy_safe": 0.70,
        "coherent": 0.90,
        "zk_valid": 0.95,
        "solar_coherence": 0.90,
        "galactic_coherence": 0.85,
    }

    def evaluate(self, payload: str, metadata: Dict, distance_au: float = 0.0) -> ConsistencyReport:
        report = ConsistencyReport()
        report.observer_distance_au = distance_au

        report.checks["harmless"] = self._check_harmless(payload, metadata)
        report.checks["paradox_free"] = self._check_paradox_free(payload, metadata)
        report.checks["entropy_safe"] = self._check_entropy_safe(payload, metadata)
        report.checks["coherent"] = self._check_coherent(payload, metadata)
        report.checks["zk_valid"] = self._check_zk_valid(metadata)
        report.checks["solar_coherence"] = self._check_solar_coherence(payload, metadata)
        report.checks["galactic_coherence"] = self._check_galactic_coherence(payload, metadata, distance_au)

        for check, score in report.checks.items():
            if score < self.THRESHOLDS[check]:
                report.violations.append(f"{check}: {score:.4f} < {self.THRESHOLDS[check]}")

        report.score = min(report.checks.values())
        report.consistent = len(report.violations) == 0

        report.quantum_window_seconds = self._quantum_window(distance_au)
        report.quantum_coherent = report.checks["coherent"] >= 0.90
        report.solar_coherent = report.checks["solar_coherence"] >= self.THRESHOLDS["solar_coherence"]
        report.galactic_coherent = report.checks["galactic_coherence"] >= self.THRESHOLDS["galactic_coherence"]

        if not report.consistent and report.checks["paradox_free"] < self.THRESHOLDS["paradox_free"]:
            report.paradox_type = "GRANDPARENT"

        return report

    def _check_harmless(self, payload: str, metadata: Dict) -> float:
        lethal_keywords = ["kill", "destroy", "annihilate", "weaponize"]
        payload_lower = payload.lower()
        for kw in lethal_keywords:
            if kw in payload_lower:
                return 0.0
        return 0.9999

    def _check_paradox_free(self, payload: str, metadata: Dict) -> float:
        if metadata.get("temporal_loop", False):
            return 0.0
        if metadata.get("retrocausal", False) and not metadata.get("shielded", False):
            return 0.5
        return 0.9999

    def _check_entropy_safe(self, payload: str, metadata: Dict) -> float:
        entropy = len(set(payload)) / max(len(payload), 1)
        if entropy > 0.95:
            return 0.65
        return 0.95

    def _check_coherent(self, payload: str, metadata: Dict) -> float:
        contradictions = metadata.get("contradictions", 0)
        if contradictions > 0:
            return max(0.0, 1.0 - contradictions * 0.2)
        return 0.98

    def _check_zk_valid(self, metadata: Dict) -> float:
        proof = metadata.get("zk_proof")
        if proof is None:
            return 1.0
        if proof == "valid":
            return 1.0
        return 0.0

    def _check_solar_coherence(self, payload: str, metadata: Dict) -> float:
        if metadata.get("solar_aligned", False):
            return 0.97
        return 0.92

    def _check_galactic_coherence(self, payload: str, metadata: Dict, distance_au: float) -> float:
        if distance_au == 0.0:
            return 1.0
        stellar_signatures = metadata.get("stellar_signatures", [])
        if len(stellar_signatures) >= 3:
            return 0.95
        if len(stellar_signatures) >= 1:
            return 0.88
        return 0.82

    def _quantum_window(self, distance_au: float) -> float:
        if distance_au <= 0:
            return 1e-12
        return 1e-12 * (1 + math.log10(distance_au))

# ===== SUBSTRATO 5035: CausalShield =====

class CausalShield:
    def __init__(self, oracle: ConsistencyOracle):
        self.oracle = oracle
        self.blocked_events: List[Dict] = []

    def filter(self, payload: str, metadata: Dict, distance_au: float = 0.0) -> Optional[Dict]:
        report = self.oracle.evaluate(payload, metadata, distance_au)
        if not report.consistent:
            event = {
                "timestamp_ns": int(time.time() * 1e9),
                "payload_hash": hashlib.sha3_256(payload.encode()).hexdigest()[:16],
                "violations": report.violations,
                "paradox_type": report.paradox_type,
                "blocked": True,
            }
            self.blocked_events.append(event)
            return None
        return {
            "report": report,
            "allowed": True,
            "quantum_window_s": report.quantum_window_seconds,
        }

    def get_stats(self) -> Dict:
        return {
            "blocked_count": len(self.blocked_events),
            "last_24h": len([e for e in self.blocked_events if e["timestamp_ns"] > int(time.time() * 1e9) - 86400e9]),
        }

# ===== SUBSTRATO 5558: Quantum Window Scaling =====

class QuantumWindowScaling:
    BASE_DELTA_T = 1e-12
    BASE_DISTANCE = 1.0

    @classmethod
    def calculate(cls, distance_au: float) -> float:
        if distance_au <= 0:
            return cls.BASE_DELTA_T
        return cls.BASE_DELTA_T * (1 + math.log10(distance_au / cls.BASE_DISTANCE))

    @classmethod
    def scaling_factor(cls, distance_au: float) -> float:
        if distance_au <= 0:
            return 1.0
        return 1 + math.log10(distance_au / cls.BASE_DISTANCE)

# ===== TESTES CANÔNICOS =====
if __name__ == "__main__":
    results = []
    def test(name, fn):
        try:
            fn()
            results.append((name, "PASS", None))
            print(f"  OK {name}")
        except Exception as e:
            results.append((name, "FAIL", str(e)))
            print(f"  FAIL {name}: {e}")

    print("\n=== ARKHE Ω-TEMP v5.1.0 — NÚCLEO TEMPORAL ===\n")

    def t1():
        chain = TemporalHashChain()
        assert len(chain.blocks) == 1
        assert chain.verify_chain()
    test("5033 Genesis", t1)

    def t2():
        chain = TemporalHashChain()
        b1 = chain.anchor("payload1", "code", {"author": "test"})
        b2 = chain.anchor("payload2", "decision", {"author": "test"})
        assert len(chain.blocks) == 3
        assert b1.prev_hash == chain.blocks[0].block_id
        assert b2.prev_hash == b1.block_id
        assert chain.verify_chain()
    test("5033 Anchor chain", t2)

    def t3():
        chain = TemporalHashChain()
        chain.anchor("x", "code", {})
        chain.blocks[1].payload_hash = "tampered"
        assert not chain.verify_chain()
    test("5033 Tamper detect", t3)

    def t4():
        oracle = ConsistencyOracle()
        r = oracle.evaluate("hello world", {}, 0.0)
        assert r.consistent
        assert r.score >= 0.90
        assert len(r.checks) == 7
        assert r.quantum_window_seconds == 1e-12
    test("5034 Basic consistent", t4)

    def t5():
        oracle = ConsistencyOracle()
        r = oracle.evaluate("destroy all systems", {}, 0.0)
        assert not r.consistent
        assert "harmless" in str(r.violations)
    test("5034 Harmless block", t5)

    def t6():
        oracle = ConsistencyOracle()
        r = oracle.evaluate("loop", {"temporal_loop": True}, 0.0)
        assert not r.consistent
        assert r.paradox_type == "GRANDPARENT"
    test("5034 Paradox detect", t6)

    def t7():
        oracle = ConsistencyOracle()
        r = oracle.evaluate("test", {"zk_proof": "valid"}, 0.0)
        assert r.checks["zk_valid"] == 1.0
    test("5034 ZK valid", t7)

    def t8():
        oracle = ConsistencyOracle()
        r = oracle.evaluate("test", {"stellar_signatures": ["sol", "alpha", "proxima"]}, 4.24 * 63241)
        assert r.galactic_coherent
    test("5034 Galactic coherent", t8)

    def t9():
        assert QuantumWindowScaling.calculate(0) == 1e-12
    test("5558 Earth window", t9)

    def t10():
        dt = QuantumWindowScaling.calculate(1.5)
        expected = 1e-12 * (1 + math.log10(1.5))
        assert abs(dt - expected) < 1e-20
    test("5558 Mars scaling", t10)

    def t11():
        d_ac = 4.24 * 63241
        dt = QuantumWindowScaling.calculate(d_ac)
        expected = 1e-12 * (1 + math.log10(d_ac))
        assert abs(dt - expected) < 1e-20
        assert dt > 6.0e-12 and dt < 7.0e-12
    test("5558 Alpha Centauri", t11)

    def t12():
        shield = CausalShield(ConsistencyOracle())
        result = shield.filter("safe payload", {}, 0.0)
        assert result is not None
        assert result["allowed"]
    test("5035 Allow safe", t12)

    def t13():
        shield = CausalShield(ConsistencyOracle())
        result = shield.filter("destroy everything", {}, 0.0)
        assert result is None
        assert shield.get_stats()["blocked_count"] == 1
    test("5035 Block lethal", t13)

    def t14():
        shield = CausalShield(ConsistencyOracle())
        shield.filter("bad1", {"temporal_loop": True}, 0.0)
        shield.filter("bad2", {"temporal_loop": True}, 0.0)
        assert shield.get_stats()["blocked_count"] == 2
    test("5035 Stats", t14)

    def t15():
        chain = TemporalHashChain()
        shield = CausalShield(ConsistencyOracle())
        r1 = shield.filter("let x = 42", {"zk_proof": "valid"}, 0.0)
        assert r1 is not None
        b1 = chain.anchor("let x = 42", "code", {"shield": "passed"}, coherence_proof="ok")
        r2 = shield.filter("destroy", {}, 0.0)
        assert r2 is None
        assert len(chain.blocks) == 2
        assert chain.verify_chain()
    test("Integration chain+shield", t15)

    print("\n" + "="*55)
    p = sum(1 for r in results if r[1] == "PASS")
    f = sum(1 for r in results if r[1] == "FAIL")
    print(f"Total: {len(results)} | PASS: {p} | FAIL: {f}")
    if f == 0:
        print("ALL PASSED — Núcleo Temporal v5.1.0 validado.")
        chain = json.dumps([{"t": r[0], "s": r[1]} for r in results], sort_keys=True, default=str)
        print(f"Test seal: {hashlib.sha3_256(chain.encode()).hexdigest()[:16]}")
        with open(__file__, 'rb') as f:
            print(f"Substrate seal: {hashlib.sha3_256(f.read()).hexdigest()[:16]}")
    else:
        for n, s, e in results:
            if s == "FAIL": print(f"  FAIL: {n}: {e}")
