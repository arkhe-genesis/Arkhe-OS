#!/usr/bin/env python3
"""
Automated P1-P5 compliance check for QuantumGrok Engine v∞.393.1.
Fails fast if any epistemic standard is violated.
"""
import json
import sys
from pathlib import Path

def validate_p1_p5(report_path: str) -> bool:
    with open(report_path) as f:
        report = json.load(f)

    checks = {'P1': False, 'P2': False, 'P3': False, 'P4': False, 'P5': False}

    # P1: Lattice and gauge representation explicit & hashed
    lattice = report.get('p1_lattice', {})
    gauge = report.get('p1_gauge', {})
    checks['P1'] = bool(lattice.get('hash')) and gauge.get('unitarity_check') == 'passed_by_construction'

    # P2: Chern-Simons error model quantified
    cs = report.get('p2_chern_simons', {})
    checks['P2'] = 'error_estimate' in cs and 'topological_charge' in cs

    # P3: Full pipeline metadata present
    checks['P3'] = all(k in report for k in ['version', 'status', 'p1_lattice', 'p2_chern_simons'])

    # P4: Reproducibility config complete
    rep = report.get('p4_reproducibility', {})
    checks['P4'] = all(k in rep for k in ['seed_numpy', 'seed_torch', 'mp_dps', 'voxel_grid', 'dependencies'])

    # P5: Conventions explicit
    conv = report.get('p5_conventions', {})
    checks['P5'] = all(k in conv for k in ['units', 'observable_mapping', 'boundary_conditions'])

    all_pass = all(checks.values())
    print(f"\n🔍 P1-P5 COMPLIANCE CHECK (Substrate 103):")
    for k, v in checks.items():
        status = "✅" if v else "❌"
        print(f"  {status} {k}: {'PASS' if v else 'FAIL'}")
    print(f"  {'✅ ALL P1-P5 CHECKS PASSED' if all_pass else '❌ COMPLIANCE VIOLATION DETECTED'}")
    return all_pass

if __name__ == '__main__':
    report_file = 'results/quantumgrok_v393_run_latest.json'
    if not Path(report_file).exists():
        print(f"⚠️ Run pipeline first: python core/quantumgrok_engine_v2.py")
        sys.exit(1)

    if validate_p1_p5(report_file):
        print("\n✅ Report ready for external review / archival.")
    else:
        print("\n❌ Fix P1-P5 compliance before proceeding.")
        sys.exit(1)
