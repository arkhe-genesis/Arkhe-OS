import hashlib, json, time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple

class Severity(Enum):
    PASS = auto()
    WARN = auto()
    FAIL = auto()
    CRITICAL = auto()

@dataclass(frozen=True)
class ConstitutionalProof:
    timestamp: float
    platform_hash: str
    module: str
    invariant: str
    severity: str
    message: str
    details: str
    signature: str

    def __post_init__(self):
        payload = "|".join([
            str(self.timestamp), self.platform_hash, self.module,
            self.invariant, self.severity, self.message, self.details
        ])
        expected = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
        if self.signature != expected:
            raise ValueError("Assinatura invalida para " + self.invariant)

    def verify(self) -> bool:
        payload = "|".join([
            str(self.timestamp), self.platform_hash, self.module,
            self.invariant, self.severity, self.message, self.details
        ])
        expected = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
        return self.signature == expected

@dataclass
class VerificationResult:
    module: str
    checks: List[Tuple] = field(default_factory=list)
    proofs: List[ConstitutionalProof] = field(default_factory=list)

    def generate_proofs(self, platform_hash: str):
        proofs = []
        ts = time.time()
        for inv, sev, msg, det in self.checks:
            det_str = json.dumps(det, sort_keys=True)
            payload = "|".join([
                str(ts), platform_hash, self.module,
                inv, sev.name, msg, det_str
            ])
            sig = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
            proofs.append(ConstitutionalProof(
                timestamp=ts, platform_hash=platform_hash,
                module=self.module, invariant=inv, severity=sev.name,
                message=msg, details=det_str, signature=sig
            ))
        self.proofs = proofs
        return proofs

    def compute_phi_c(self) -> float:
        total = len(self.checks)
        if total == 0:
            return 1.0
        passed = sum(1 for _, sev, _, _ in self.checks if sev == Severity.PASS)
        return passed / total