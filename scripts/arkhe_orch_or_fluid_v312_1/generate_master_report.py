#!/usr/bin/env python3
"""
generate_master_report.py
Gera um relatório markdown master dos resultados.
"""
import json
import glob
import argparse
import os

def generate_report(results_pattern):
    files = glob.glob(results_pattern)
    if not files:
        print(f"No files found matching {results_pattern}")
        return
    latest_file = max(files, key=os.path.getctime)
    with open(latest_file, 'r') as f:
        results = json.load(f)

    report = f"""# 🧠🌊 ARKHE OS v∞.312.1 — ORCH-OR FLUIDIC MASTER REPORT

**Timestamp:** {results['metadata']['timestamp']}
**Framework:** {results['metadata']['framework']}

## Test 1: Mass Dependence (Pressure Projection Collapse)
* **Interpretation:** {results['tests']['mass_dependence']['interpretation']}
* **p-value:** {results['tests']['mass_dependence']['p_value_mass_dependence']:.4f}

## Test 2: Intention Modulation (0.58 Vortex)
* **Significant:** {'Yes' if results['tests']['intention_modulation']['significant'] else 'No'}
* **Pearson r:** {results['tests']['intention_modulation']['pearson_r']:.3f}
* **p-value (FDR):** {results['tests']['intention_modulation']['p_value_fdr_corrected']:.4f}

## Test 3: Non-associative Collapse Statistics
* **Interpretation:** {results['tests']['nonassociative_stats']['interpretation']}
* **Any significant:** {'Yes' if results['tests']['nonassociative_stats']['any_significant'] else 'No'}

## Cross-Validation & Evidence
* **Overall Consistency:** {results['cross_validation']['overall_consistency']}
* **Combined Bayes Factor:** {results['combined_evidence']['bayes_factor_combined']:.2f} ({results['combined_evidence']['interpretation']})
"""

    with open('master_report.md', 'w') as f:
        f.write(report)
    print("Master report generated: master_report.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', default='results/orch_or_fluid_integrated_*.json')
    args = parser.parse_args()
    generate_report(args.results)
