#!/usr/bin/env python3
"""
Arkhe Constitutional Verifier v2.1 — Windows Native Edition
Paths Windows, Event Log, e logging append-only.
"""

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Dict, Tuple
import logging
import logging.handlers

class ConstitutionalVerifierWindows:
    GHOST_THRESHOLD = 0.577350
    LOOPSEAL_THRESHOLD = 0.349066
    GAP_THRESHOLD = 0.999900

    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
        self.results = []
        self.start_time = time.time()

        # Logger dual: arquivo append-only + Windows Event Log
        self.logger = logging.getLogger('Arkhe-Constitution')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(r"C:\Arkhe\Logs\constitution.log")
            fh.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(fh)
            try:
                eh = logging.handlers.NTEventLogHandler("Arkhe-Constitution")
                eh.setFormatter(logging.Formatter('%(message)s'))
                self.logger.addHandler(eh)
            except ImportError:
                pass

    def verify_all(self) -> Tuple[bool, Dict]:
        checks = {
            "substrate_integrity": self._verify_substrate_hashes(),
            "runtime_policies": self._verify_runtime_policies(),
            "proof_logs": self._verify_proof_logs(),
        }
        phi_c = self._compute_phi_c(checks)
        checks["principles"] = (
            phi_c > self.GHOST_THRESHOLD and
            phi_c > self.LOOPSEAL_THRESHOLD and
            phi_c <= self.GAP_THRESHOLD
        )
        all_pass = all(v for v in checks.values())
        result = {
            "timestamp": time.time(),
            "duration_seconds": time.time() - self.start_time,
            "checks": checks,
            "phi_c": phi_c,
            "all_pass": all_pass,
            "status": "PASS" if all_pass else "FAIL"
        }
        self._log_result(result)
        self.results.append(result)
        return all_pass, result

    def _verify_substrate_hashes(self) -> bool:
        manifest = Path(r"C:\Arkhe\Proofs\manifest.sha3")
        if not manifest.exists():
            return False
        with open(manifest, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('  ', 1)
                if len(parts) != 2:
                    continue
                expected_hash, filename = parts
                filepath = Path(filename.lstrip('*'))
                if not filepath.exists():
                    if not self.quick_mode:
                        return False
                    continue
                with open(filepath, 'rb') as fsub:
                    actual = hashlib.sha3_256(fsub.read()).hexdigest()
                if actual != expected_hash.lower():
                    return False
        return True

    def _verify_runtime_policies(self) -> bool:
        policies = [
            Path(r"C:\Arkhe\Config\seccomp-arkhe.json"),
            Path(r"C:\Arkhe\Config\capabilities-drop.txt"),
        ]
        for policy in policies:
            if not policy.exists() and not self.quick_mode:
                return False
        return True

    def _verify_proof_logs(self) -> bool:
        return Path(r"C:\Arkhe\Proofs").exists() and Path(r"C:\Arkhe\Logs").exists()

    def _compute_phi_c(self, checks: Dict[str, bool]) -> float:
        import numpy as np
        weights = np.ones(18) / 18  # Substituir por MANIFEST_V1_0_WEIGHTS
        scores = np.array([
            1.0 if checks.get("substrate_integrity", False) else 0.0,
            1.0 if checks.get("runtime_policies", False) else 0.0,
            1.0 if checks.get("proof_logs", False) else 0.0,
            1.0 if checks.get("principles", False) else 0.0,
        ] + [0.0] * 14)
        return float(np.dot(scores, weights))

    def _log_result(self, result: Dict):
        msg = json.dumps(result)
        self.logger.info(msg)
        print(msg, file=sys.stderr)


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    v = ConstitutionalVerifierWindows(quick_mode=quick)
    passed, result = v.verify_all()
    print(json.dumps(result, indent=2))
    sys.exit(0 if passed else 1)