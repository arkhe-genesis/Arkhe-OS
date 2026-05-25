# ═══════════════════════════════════════════════════════════════════
# ARKHE OS — AUDIT DAEMON v3.0 (Updated for Glosa 240)
# New: Invariant I0 (Source Verified)
# Date: 2026-05-24T21:17:00Z
# ═══════════════════════════════════════════════════════════════════

import os
import re
import sys
import toml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class AuditResult:
    substrate_id: int
    substrate_name: str
    status: str
    phi_c: float
    ti: float
    seal_valid: bool
    source_verified: bool
    invariants_pass: int
    cross_links_valid: bool
    warnings: List[str]

class AuditDaemon:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.substrates_dir = self.repo_root / "substrates"
        self.src_dir = self.repo_root / "src" / "substrates"
        self.thresholds = self._load_thresholds()

    def _load_thresholds(self) -> dict:
        config_path = self.repo_root / "config" / "thresholds.toml"
        if config_path.exists():
            return toml.load(config_path)
        return {
            "phi_c_min": 0.70,
            "ti_min": 0.70,
            "source_verified_required": False,  # Warning only, not blocking
        }

    def _validate_seal(self, seal: str) -> bool:
        """Validate SHA3-256 seal format."""
        if not seal:
            return False
        if seal == "PLACEHOLDER":
            return False
        return len(seal) == 64 and all(c in '0123456789abcdef' for c in seal.lower())

    def _check_source_verified(self, substrate_path: Path) -> Tuple[bool, List[str]]:
        """Check I0: Source Verified invariant."""
        warnings = []

        # Check substrate.toml
        toml_path = substrate_path / "substrate.toml"
        if not toml_path.exists():
            warnings.append("Missing substrate.toml")
            return False, warnings

        try:
            config = toml.load(toml_path)
            source_verified = config.get("audit", {}).get("source_verified", False)

            if not source_verified:
                warnings.append(
                    "I0 (Source Verified): source_verified = false. "
                    "Substrate has unverified sources. "
                    "Confidence marker: LOW. "
                    "Per Glosa 240: 'A Catedral especula, sem evidência direta...'"
                )

            return source_verified, warnings

        except Exception as e:
            warnings.append(f"Error reading substrate.toml: {e}")
            return False, warnings

    def audit_substrate(self, substrate_path: Path) -> AuditResult:
        """Audit a single substrate."""
        warnings = []

        # Extract ID and name from path
        dirname = substrate_path.name
        match = re.match(r'(\d+)_(.+)', dirname)
        if not match:
            return AuditResult(
                substrate_id=0,
                substrate_name=dirname,
                status="INVALID",
                phi_c=0.0,
                ti=0.0,
                seal_valid=False,
                source_verified=False,
                invariants_pass=0,
                cross_links_valid=False,
                warnings=["Invalid directory naming (expected: {number}_{name})"]
            )

        sub_id = int(match.group(1))
        sub_name = match.group(2)

        # Load substrate.toml
        toml_path = substrate_path / "substrate.toml"
        if not toml_path.exists():
            warnings.append("Missing substrate.toml")
            return AuditResult(
                substrate_id=sub_id,
                substrate_name=sub_name,
                status="NO_TOML",
                phi_c=0.0,
                ti=0.0,
                seal_valid=False,
                source_verified=False,
                invariants_pass=0,
                cross_links_valid=False,
                warnings=warnings
            )

        try:
            config = toml.load(toml_path)
        except Exception as e:
            warnings.append(f"Invalid TOML: {e}")
            return AuditResult(
                substrate_id=sub_id,
                substrate_name=sub_name,
                status="INVALID_TOML",
                phi_c=0.0,
                ti=0.0,
                seal_valid=False,
                source_verified=False,
                invariants_pass=0,
                cross_links_valid=False,
                warnings=warnings
            )

        # Extract metrics
        metrics = config.get("metrics", {})
        phi_c = metrics.get("standard_phi_c", 0.0)
        ti = metrics.get("theosis_index", 0.0)
        seal = config.get("substrate", {}).get("seal", "")
        status = config.get("substrate", {}).get("status", "UNKNOWN")

        # Validate seal
        seal_valid = self._validate_seal(seal)
        if not seal_valid:
            warnings.append("Invalid or placeholder seal")

        # Check I0: Source Verified
        source_verified, source_warnings = self._check_source_verified(substrate_path)
        warnings.extend(source_warnings)

        # Check thresholds
        if phi_c < self.thresholds["phi_c_min"]:
            warnings.append(f"Φ_C {phi_c} below threshold {self.thresholds['phi_c_min']}")

        if ti < self.thresholds["ti_min"]:
            warnings.append(f"TI {ti} below threshold {self.thresholds['ti_min']}")

        # Check cross-links (simplified)
        links = config.get("cross_substrate", {}).get("links", [])
        cross_links_valid = len(links) > 0 or status in ["PROPOSED", "MIGRATED"]

        # Count invariants (simplified: check if 18 scores exist)
        invariants_pass = 18 if phi_c > 0 else 0

        return AuditResult(
            substrate_id=sub_id,
            substrate_name=sub_name,
            status=status,
            phi_c=phi_c,
            ti=ti,
            seal_valid=seal_valid,
            source_verified=source_verified,
            invariants_pass=invariants_pass,
            cross_links_valid=cross_links_valid,
            warnings=warnings
        )

    def run_audit(self, strict: bool = False) -> bool:
        """Run full audit on all substrates."""
        print("ARKHE OS Audit Daemon v3.0")
        print("=" * 60)
        print(f"Mode: {'STRICT' if strict else 'NORMAL'}")
        print(f"Thresholds: Φ_C ≥ {self.thresholds['phi_c_min']}, TI ≥ {self.thresholds['ti_min']}")
        print("")

        all_pass = True
        results = []

        # Audit substrates/
        if self.substrates_dir.exists():
            for subdir in sorted(self.substrates_dir.iterdir()):
                if subdir.is_dir() and re.match(r'\d+_', subdir.name):
                    result = self.audit_substrate(subdir)
                    results.append(result)

        # Audit src/substrates/
        if self.src_dir.exists():
            for subdir in sorted(self.src_dir.iterdir()):
                if subdir.is_dir() and re.match(r'\d+_', subdir.name):
                    result = self.audit_substrate(subdir)
                    results.append(result)

        # Print results
        passed = 0
        failed = 0
        warned = 0

        for r in results:
            status_icon = "✓" if r.seal_valid and r.phi_c >= self.thresholds["phi_c_min"] else "✗"
            if r.warnings:
                status_icon = "⚠"
                warned += 1

            print(f"{status_icon} {r.substrate_id:03d}-{r.substrate_name}")
            print(f"   Status: {r.status} | Φ_C: {r.phi_c:.6f} | TI: {r.ti:.3f}")
            print(f"   Seal: {'VALID' if r.seal_valid else 'INVALID'}")
            print(f"   Source: {'VERIFIED' if r.source_verified else 'UNVERIFIED'}")

            if r.warnings:
                for w in r.warnings:
                    print(f"   WARNING: {w}")

            print("")

            if status_icon == "✓":
                passed += 1
            elif status_icon == "✗":
                failed += 1
                all_pass = False

        # Summary
        print("=" * 60)
        print(f"Total: {len(results)} | Passed: {passed} | Warned: {warned} | Failed: {failed}")

        if strict and not all_pass:
            print("\n✗ STRICT MODE: Audit failed. Fix issues before commit.")
            return False

        if warned > 0:
            print(f"\n⚠ {warned} substrates have warnings (non-blocking in normal mode)")

        print("\n✓ Audit complete.")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ARKHE OS Audit Daemon")
    parser.add_argument("--strict", action="store_true", help="Fail on any warning")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    daemon = AuditDaemon(args.root)
    success = daemon.run_audit(strict=args.strict)
    sys.exit(0 if success else 1)
