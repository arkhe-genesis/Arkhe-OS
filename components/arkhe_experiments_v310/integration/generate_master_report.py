#!/usr/bin/env python3
"""
integration/generate_master_report.py
Gera relatório integrado formatado para submissão científica.
"""
import json
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

def generate_master_report(results_path: str, output_dir: str = 'docs/reports'):
    """Gera relatório em Markdown + figuras para publicação."""

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_results_path = os.path.join(base_dir, results_path) if not os.path.isabs(results_path) else results_path
    full_output_dir = os.path.join(base_dir, output_dir)

    with open(full_results_path, 'r') as f:
        results = json.load(f)

    report = f"""# ARKHE OS v∞.310 — Integrated Experimental Results
**Timestamp**: {results['metadata']['timestamp']}
**Version**: {results['metadata']['version']}
**Config**: {results['metadata']['config']}

---

## Executive Summary
{results.get('combined_evidence', {}).get('interpretation', 'Analysis in progress')}

Combined Bayes factor: **{results.get('combined_evidence', {}).get('bayes_factor_combined', 'N/A'):.2f}**

---

## Track 1: Mass-Dependence Test (τ ∝ 1/√N)

### Hypotheses
- **Orch‑OR prediction**: τ = a/√N + b with a > 0 (gravitational collapse)
- **Conventional prediction**: τ ≈ constant (environmental decoherence)

### Results
"""

    track1 = results['tracks'].get('mass_dependence', {})
    if 'error' not in track1:
        fit = track1.get('fit_results', {})
        report += f"""
- Fitted parameters: a = {fit.get('a', 'N/A')} ± {fit.get('a_err', 'N/A')}, b = {fit.get('b', 'N/A')} ± {fit.get('b_err', 'N/A')}
- Frequentist test: t(a) = {track1.get('frequentist_test', {}).get('t_stat_a', 'N/A')}, p = {track1.get('frequentist_test', {}).get('p_value_mass_dependence', 'N/A')}
- Bayesian evidence: BF ≈ {track1.get('bayesian_evidence', {}).get('bayes_factor_approx', 'N/A')} ({track1.get('bayesian_evidence', {}).get('interpretation', 'N/A')})
"""
    else:
        report += f"\n- Error: {track1['error']}\n"

    track2 = results['tracks'].get('intention_correlation', {})
    report += f"""
---

## Track 2: Intention Correlation Test

### Results
{track2.get('interpretation', 'N/A')}
"""

    track3 = results['tracks'].get('nonassociative_stats', {})
    report += f"""
---

## Track 3: Non-Associative Statistics Test

### Results
{track3.get('interpretation', 'N/A')}
"""

    report += f"""
---

## Cross-Validation & Combined Evidence

### Consistency Between Tracks
- Mass-dependence evidence level: {results.get('cross_validation', {}).get('mass_evidence_level', 'N/A')}
- Non-associativity significant: {results.get('cross_validation', {}).get('nonassoc_significant', 'N/A')}
- Overall consistency: **{results.get('cross_validation', {}).get('overall_consistency', 'N/A')}**

### Combined Bayesian Evidence
- Individual Bayes factors: {results.get('combined_evidence', {}).get('individual_bayes_factors', [])}
- **Combined BF**: {results.get('combined_evidence', {}).get('bayes_factor_combined', 'N/A')}
- Interpretation: **{results.get('combined_evidence', {}).get('interpretation', 'N/A')}**

---

## Conclusions & Next Steps

{results.get('combined_evidence', {}).get('interpretation', 'Analysis in progress').capitalize()}.

**Recommended next steps**:
1. Replicate with independent data/seed
2. Pre-register follow-up study on OSF
3. Submit to peer-reviewed journal (e.g., *Foundations of Physics*, *Consciousness and Cognition*)

---

## Reproducibility

All code and data available at: [ARKHE GitHub repository](https://github.com/arkhe-os/experiments-v310)
Analysis pipeline: `integration/run_all_tracks.py`
Statistical plan: `config/statistical_plan.json`

*Report generated automatically by ARKHE OS v∞.310*
"""

    os.makedirs(full_output_dir, exist_ok=True)
    report_path = os.path.join(full_output_dir, f"master_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 Relatório master gerado: {report_path}")
    return report_path

if __name__ == "__main__":
    import argparse
    import glob
    parser = argparse.ArgumentParser()
    parser.add_argument('--results')
    args = parser.parse_args()

    results_file = args.results
    if not results_file or '*' in results_file:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Find latest results file
        files = glob.glob(os.path.join(base_dir, 'data/processed/integrated_results_*.json'))
        if files:
            results_file = max(files, key=os.path.getctime)
        else:
            print("No results file found.")
            sys.exit(1)

    generate_master_report(results_file)
