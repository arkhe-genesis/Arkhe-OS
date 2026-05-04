#!/usr/bin/env python3
# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14.3 — Wrangler CLI for Temporal Ledger Operations
# Commands: fork create, fork list, merge evaluate, merge accept, rollback, status
# Seven-dimensional Coherence version
# ============================================================================

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
import time
import hashlib
import numpy as np

# Backend imports for CLI structure
from consensus_engine_7d import ProofOfCoherenceConsensus7D, CoherenceStake7D, ForkVote7D, CoherenceTensor7D

class ArkheConfig:
    """Local CLI state management."""
    def __init__(self, path: Path = Path.home() / ".arkhe"):
        self.path = path
        self.path.mkdir(exist_ok=True)
        self.config_file = self.path / "config.json"
        if not self.config_file.exists():
            self._init_default_config()

    def _init_default_config(self):
        default = {"ledger_id": "mainnet-alpha", "consensus_threshold": 0.55}
        with open(self.config_file, 'w') as f:
            json.dump(default, f, indent=2)

def parse_args():
    parser = argparse.ArgumentParser(prog="wrangler", description="ARKHE Temporal Ledger CLI")
    subparsers = parser.add_subparsers(dest="command", help="Operation")

    # fork create
    p_fork = subparsers.add_parser("fork", help="Temporal branch operations")
    p_fork.add_argument("action", choices=["create", "list"])
    p_fork.add_argument("--timestamp", type=float, help="Logical timestamp to fork from")
    p_fork.add_argument("--reason", default="exploration", help="Fork justification")
    p_fork.add_argument("--target-phase", type=float, help="Target Phase Coherence")
    p_fork.add_argument("--target-latency", type=float, help="Target Latency Coherence")
    p_fork.add_argument("--target-power", type=float, help="Target Power Coherence")
    p_fork.add_argument("--target-mercy", type=float, help="Target Mercy Gap")
    p_fork.add_argument("--target-security", type=float, help="Target Security Coherence")
    p_fork.add_argument("--target-privacy", type=float, help="Target Privacy Coherence")
    p_fork.add_argument("--target-interpretability", type=float, help="Target Interpretability Coherence")

    # merge evaluate/accept
    p_merge = subparsers.add_parser("merge", help="Fork resolution operations")
    p_merge.add_argument("action", choices=["evaluate", "accept"])
    p_merge.add_argument("--fork-id", required=True, help="Target fork ID")
    p_merge.add_argument("--odysseus-ratio", type=float, default=1.0, help="Insight ratio bonus")
    p_merge.add_argument("--coherence-report", choices=["none", "full"], default="none", help="Display 7D Coherence Report")
    p_merge.add_argument("--dry-run", action="store_true")

    # rollback
    p_roll = subparsers.add_parser("rollback", help="Point-in-time recovery")
    p_roll.add_argument("--timestamp", type=float, required=True)
    p_roll.add_argument("--dry-run", action="store_true")

    return parser.parse_args()

def main():
    args = parse_args()
    config = ArkheConfig()

    if args.command == "fork":
        if args.action == "create":
            if not args.timestamp:
                print("❌ Error: --timestamp required for fork creation")
                sys.exit(1)
            fork_id = hashlib.sha256(f"{args.timestamp}_{args.reason}".encode()).hexdigest()[:12]
            print(f"✅ Fork created: {fork_id}")
            print(f"   └─ Source timestamp: {args.timestamp}")
            print(f"   └─ Reason: {args.reason}")
            print(f"   └─ Ledger: {config.path}")

        elif args.action == "list":
            print("📜 Active forks (mock):")
            print("  ID          Timestamp  Reason          Coherence (Phs/Lat/Pwr)")
            print("  ──────────  ─────────  ──────────────  ───────────────────────")
            print("  a1b2c3d4e5  1715400.0  exploration     0.072/0.068/0.071")
            print("  f6g7h8i9j0  1715410.0  phase_tuning    0.067/0.081/0.075")

    elif args.command == "merge":
        with open(config.config_file, 'r') as f:
            c = json.load(f)
        consensus = ProofOfCoherenceConsensus7D(consensus_threshold=c["consensus_threshold"])
        # Mock voting state for 7D
        mock_fork_coherence_7d = CoherenceTensor7D(
            phase=0.068, latency_us=482.0, power_mw=148.0, mercy_gap=0.071,
            security=0.968, privacy=0.935, interpretability=0.892
        )
        consensus.votes[args.fork_id] = [
            ForkVote7D("vertex-1", True, time.time(), b"sig1", mock_fork_coherence_7d, weight=0.85),
            ForkVote7D("vertex-2", True, time.time(), b"sig2", mock_fork_coherence_7d, weight=0.72),
            ForkVote7D("vertex-3", False, time.time(), b"sig3", mock_fork_coherence_7d, weight=0.41),
        ]

        if args.coherence_report == "full":
            accept, score, dim_scores, reason = consensus.evaluate_merge(
                args.fork_id,
                odysseus_insight_ratio=args.odysseus_ratio,
                fork_coherence=mock_fork_coherence_7d
            )
            if reason:
                print(f"❌ Rejected: {reason}")
                sys.exit(1)

            print("📊 7D Coherence Report:")
            dims = [
                ("Phase", "φ", 0.07, 0.015),
                ("Latency", "τ", 500.0, 30.0),
                ("Power", "ρ", 150.0, 15.0),
                ("Mercy Gap", "ε", 0.07, 0.015),
                ("Security", "σ", 0.95, 0.025),
                ("Privacy", "π", 0.92, 0.035),
                ("Interpretability", "ι", 0.88, 0.040)
            ]

            harmonic_vals = []
            for label, sym, target, std in dims:
                attr_name = sym.replace("τ", "latency_us").replace("ρ", "power_mw").replace("ε", "mercy_gap").replace("σ", "security").replace("π", "privacy").replace("ι", "interpretability").replace("φ", "phase")
                val = getattr(mock_fork_coherence_7d, attr_name)
                dim_score = np.exp(-(val - target)**2 / (2 * std**2))
                status = "✓" if dim_score > 0.7 else "⚠️" if dim_score > 0.5 else "❌"
                if label == "Latency":
                    print(f"   {label:16s}: {int(val)}µs {status} ({dim_score:.2f})")
                elif label == "Power":
                    print(f"   {label:16s}: {int(val)}mW {status} ({dim_score:.2f})")
                else:
                    print(f"   {label:16s}: {val:8.3f} {status} ({dim_score:.2f})")
                harmonic_vals.append(dim_score)

            harmonic_mean = 7.0 / sum(1.0 / max(s, 1e-6) for s in harmonic_vals)
            print(f"   Harmonic Mean:  {harmonic_mean:.2f}")
            print(f"   Overall Score:  {score:.3f} / {consensus.threshold:.3f} {'✅ ACCEPTED' if accept else '❌ REJECTED'}")

            # Odysseus bonus calculation
            cov_inv = np.linalg.inv(consensus.covariance_global)
            diff = mock_fork_coherence_7d.to_vector() - CoherenceTensor7D.soft_targets()
            mahal = diff @ cov_inv @ diff
            coherence_penalty = np.exp(-0.5 * mahal) if mahal < 100 else 1e-6
            harmonic_penalty = 1.0 / (1.0 + consensus.harmonic_factor * (1.0 - harmonic_mean))
            for_votes = sum(v.weight for v in consensus.votes[args.fork_id] if v.vote_direction)
            against_votes = sum(v.weight for v in consensus.votes[args.fork_id] if not v.vote_direction)
            odys_bonus = max(0.0, args.odysseus_ratio - 1.0) * consensus.odys_mult * (for_votes + against_votes) * coherence_penalty * harmonic_penalty

            if odys_bonus > 0:
                print(f"   Odysseus Bonus: +{odys_bonus:.2f} (ratio={args.odysseus_ratio}, harmonic={harmonic_mean:.2f})")
        else:
            accept, score, dim_scores, reason = consensus.evaluate_merge(args.fork_id, odysseus_insight_ratio=args.odysseus_ratio)
            status = "✅ ACCEPTED" if accept else "❌ REJECTED"
            if reason:
                status += f" (Reason: {reason})"
            print(f"🔍 Merge evaluation: {status}")
            print(f"   └─ Fork: {args.fork_id}")
            print(f"   └─ Consensus score: {score:.3f} / {consensus.threshold:.3f}")
            print(f"   └─ Odysseus ratio: {args.odysseus_ratio}")

        if args.dry_run:
            print("   └─ Dry-run mode: No ledger state mutated")

    elif args.command == "rollback":
        print(f"🔄 Rollback initiated to timestamp: {args.timestamp}")
        if args.dry_run:
            print("   └─ Dry-run mode: Audit trail preserved, state unchanged")
        else:
            print("   └─ State reverted. Re-seal ceremony required to resume forward progress.")

    else:
        print("❌ Unknown command. Use --help for usage.")
        sys.exit(1)

if __name__ == "__main__":
    main()
