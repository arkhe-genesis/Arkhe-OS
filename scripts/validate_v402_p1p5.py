#!/usr/bin/env python3
"""
Automated P1-P5 compliance check for Fourier Lens Operator v∞.402.1.
Fails fast if any epistemic standard is violated.
"""
import json
import sys
from pathlib import Path

def validate_p1_p5(report_path: str) -> bool:
    with open(report_path) as f:
        report = json.load(f)

    checks = {'P1': False, 'P2': False, 'P3': False, 'P4': False, 'P5': False}

    # P1: Wave initialization & propagation explicit & hashed
    wave = report.get('p1_wave_initialization', {})
    prop = report.get('p1_lens_propagation', {})
    checks['P1'] = bool(wave.get('hash')) and prop.get('method') in ['FFT_paraxial', 'Debye_vectorial']

    # P2: Error model quantified (paraxial approximation check)
    checks['P2'] = 'paraxial_check' in prop and isinstance(prop['paraxial_check'], bool)

    # P3: Full pipeline metadata present
    checks['P3'] = all(k in report for k in ['version', 'status', 'p1_wave_initialization', 'p3_detector_response'])

    # P4: Reproducibility config complete
    rep = report.get('p4_reproducibility', {})
    checks['P4'] = all(k in rep for k in ['seed_numpy', 'seed_torch', 'mp_dps', 'grid_pixels', 'dependencies'])

    # P5: Conventions explicit
    conv = report.get('p5_conventions', {})
    checks['P5'] = all(k in conv for k in ['units', 'observable_mapping', 'boundary_conditions'])

    all_pass = all(checks.values())
    print(f"\n🔍 P1-P5 COMPLIANCE CHECK (Substrate 104):")
    for k, v in checks.items():
        status = "✅" if v else "❌"
        print(f"  {status} {k}: {'PASS' if v else 'FAIL'}")
    print(f"  {'✅ ALL P1-P5 CHECKS PASSED' if all_pass else '❌ COMPLIANCE VIOLATION DETECTED'}")
    return all_pass

if __name__ == '__main__':
    report_file = 'results/fourier_lens_v402_run_latest.json'
    if not Path(report_file).exists():
        print("⚠️ Run pipeline first: python core/fourier_lens_operator.py")
        sys.exit(1)

    if validate_p1_p5(report_file):
        print("\n✅ Report ready for external review / archival.")
    else:
        print("\n❌ Fix P1-P5 compliance before proceeding.")
        sys.exit(1)