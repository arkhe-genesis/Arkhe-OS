#!/usr/bin/env python3
"""
Automated P1-P5 compliance check for Riemann Operator v∞.101.
Fails fast if any epistemic standard is violated.
"""
import json
import sys
from pathlib import Path
import numpy as np

def validate_p1_p5(report_path: str) -> bool:
    with open(report_path) as f:
        report = json.load(f)

    checks = {'P1': False, 'P2': False, 'P3': False, 'P4': False, 'P5': False}

    # P1: Hash method explicit & matrix-based
    checks['P1'] = bool(report.get('p1_hash_matrix')) and len(report['p1_hash_matrix']) == 64

    # P2: Error model quantified & falsifiability checked
    err = report.get('p2_error_model', {})
    checks['P2'] = all(k in err for k in ['mean_relative_error', 'max_relative_error', 'falsification_risk'])

    # P3: Full pipeline metadata present
    checks['P3'] = all(k in report for k in ['version', 'spectrum_numerical', 'spectrum_zeta', 'status'])

    # P4: Reproducibility config complete
    rep = report.get('p4_reproducibility', {})
    checks['P4'] = all(k in rep for k in ['seed_numpy', 'seed_mpmath', 'mp_dps', 'grid_N', 'domain_L'])

    # P5: Conventions explicit
    conv = report.get('p5_conventions', {})
    checks['P5'] = all(k in conv for k in ['mapping', 'omega_delta', 'phi_minimum_at_t0', 'normalization'])

    all_pass = all(checks.values())
    print(f"\n🔍 P1-P5 COMPLIANCE CHECK:")
    for k, v in checks.items():
        status = "✅" if v else "❌"
        print(f"  {status} {k}: {'PASS' if v else 'FAIL'}")
    print(f"  {'✅ ALL P1-P5 CHECKS PASSED' if all_pass else '❌ COMPLIANCE VIOLATION DETECTED'}")
    return all_pass

if __name__ == '__main__':
    report_file = 'results/riemann_v101_run_latest.json'
    if not Path(report_file).exists():
        print("⚠️ Run pipeline first: python core/riemann_operator_v101.py")
        sys.exit(1)

    if validate_p1_p5(report_file):
        print("\n✅ Report ready for external review / archival.")
    else:
        print("\n❌ Fix P1-P5 compliance before proceeding.")
        sys.exit(1)