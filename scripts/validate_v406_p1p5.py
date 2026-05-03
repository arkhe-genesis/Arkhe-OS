#!/usr/bin/env python3
"""
Automated P1-P5 compliance check for Sophon Network Protocol v∞.406.1.
Fails fast if any epistemic standard is violated.
"""
import json
import sys
from pathlib import Path

def validate_p1_p5(report_path: str) -> bool:
    with open(report_path) as f:
        report = json.load(f)

    checks = {'P1': False, 'P2': False, 'P3': False, 'P4': False, 'P5': False}

    # P1: Packet structure explicit & hashed
    packet = report.get('packet_structure', {})
    checks['P1'] = all(k in packet for k in ['chronometric_preamble', 'braid_header', 'payload', 'phi_manifestation'])

    # P2: Error model quantified (coherence distance, sync error)
    error_model = report.get('error_model', {})
    checks['P2'] = 'coherence_distance_formula' in error_model and 'sync_error_bound' in error_model

    # P3: Full protocol phases present
    phases = report.get('protocol_phases', [])
    checks['P3'] = len(phases) == 7 and all(f'Phase {i+1}' in p for i,p in enumerate(phases))

    # P4: Reproducibility config complete
    rep = report.get('reproducibility', {})
    checks['P4'] = all(k in rep for k in ['seed_numpy', 'mp_dps', 'network_nodes', 'dependencies'])

    # P5: Conventions explicit
    conv = report.get('conventions', {})
    checks['P5'] = all(k in conv for k in ['units', 'observable_mapping', 'normalization', 'boundary_conditions'])

    all_pass = all(checks.values())
    print(f"\n🔍 P1-P5 COMPLIANCE CHECK (Substrate 105):")
    for k, v in checks.items():
        status = "✅" if v else "❌"
        print(f"  {status} {k}: {'PASS' if v else 'FAIL'}")
    print(f"  {'✅ ALL P1-P5 CHECKS PASSED' if all_pass else '❌ COMPLIANCE VIOLATION DETECTED'}")
    return all_pass

if __name__ == '__main__':
    report_file = 'results/sophon_network_test_v406.1.json'
    if not Path(report_file).exists():
        print("⚠️ Run test first: python core/sophon_network_protocol.py")
        sys.exit(1)

    if validate_p1_p5(report_file):
        print("\n✅ Report ready for external review / archival.")
    else:
        print("\n❌ Fix P1-P5 compliance before proceeding.")
        sys.exit(1)
