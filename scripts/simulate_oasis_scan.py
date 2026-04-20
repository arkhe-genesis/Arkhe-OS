import argparse
import sys
import time
import os

def simulate_scan(input_path, models, scan_model, vulns, adaptive):
    print(f"🏝️  OASIS: Scanning {input_path}")
    print(f"- **Phase 1 (Lightweight Scan)**: Completed using {scan_model or 'llama3.2:3b'}.")
    if adaptive:
        print("- **Adaptive Mode**: Risk-based depth adjustment enabled.")

    time.sleep(0.5)
    deep_models = models or "gemma:7b"
    print(f"- **Phase 2 (Deep Analysis)**: Engaging model(s) {deep_models} for high-fidelity verification.")
    print(f"  Scanning for: {vulns or 'all'}")

    time.sleep(1)
    # Simulate some realistic findings based on the path
    input_str = str(input_path).lower()
    if "auth" in input_str:
        print("- **Result**: 2 vulnerabilities detected.")
        print("  - [HIGH] Broken Authentication in `auth_service.py` (line 89).")
        print("  - [MEDIUM] Insecure Cookie Attributes in `session_config.js` (line 22).")
    elif "db" in input_str or "database" in input_str:
        print("- **Result**: 1 vulnerability detected.")
        print("  - [CRITICAL] SQL Injection in `db_query.py` (line 45).")
    elif "api" in input_str:
        print("- **Result**: 1 vulnerability detected.")
        print("  - [HIGH] Insecure Direct Object Reference (IDOR) in `api/v1/user.py` (line 12).")
    else:
        print("- **Result**: No critical vulnerabilities detected in the primary scan path.")
        print("  - [INFO] 3 minor security hardening suggestions found.")

    model_name = deep_models.split(',')[0].replace(':', '_')
    print(f"\n*Executive Summary generated at security_reports/{model_name}/executive_summary.md*")

def simulate_audit(input_path):
    print(f"🏝️  OASIS Audit: Analyzing {input_path}")
    print("- **Embedding Analysis**: Generated 512 vectors using nomic-embed-text:latest.")

    # Simulate distribution analysis
    input_str = str(input_path).lower()
    if "api" in input_str or "core" in input_str:
        component = input_path.split("/")[-1] or "component"
        print(f"- **Similarity Distribution**: Anomaly detected in `{component}`. Probability: 0.87.")
        print("- **Statistical Overview**: Mean similarity 0.45, Median 0.38, Max 0.82 (Likely pattern: Path Traversal).")
    else:
        print("- **Similarity Distribution**: Baseline established. No significant outliers found.")
        print("- **Statistical Overview**: Mean similarity 0.22, Max 0.35.")

def main():
    parser = argparse.ArgumentParser(description="🏝️ OASIS Mock Simulation Script")
    parser.add_argument("--mode", choices=["scan", "audit"], help="Simulation mode (fallback for old tools)")
    parser.add_argument("--input", required=True, help="Target input path")
    parser.add_argument("--models", help="Deep analysis models")
    parser.add_argument("--scan-model", help="Initial scan model")
    parser.add_argument("--vulns", help="Vulnerability types")
    parser.add_argument("--adaptive", action="store_true", help="Use adaptive analysis")
    parser.add_argument("--audit", action="store_true", help="OASIS Audit mode flag")

    args = parser.parse_args()

    if args.audit or args.mode == "audit":
        simulate_audit(args.input)
    else:
        simulate_scan(args.input, args.models, args.scan_model, args.vulns, args.adaptive)

if __name__ == "__main__":
    main()
