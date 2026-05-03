#!/usr/bin/env python3
# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14.1 — Wrangler CLI for Temporal Ledger Operations
# Commands: fork create, fork list, merge evaluate, merge accept, rollback, status
# Multi-dimensional version
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
from consensus_engine import ProofOfCoherenceConsensus, CoherenceStake, ForkVote

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

    # merge evaluate/accept
    p_merge = subparsers.add_parser("merge", help="Fork resolution operations")
    p_merge.add_argument("action", choices=["evaluate", "accept"])
    p_merge.add_argument("--fork-id", required=True, help="Target fork ID")
    p_merge.add_argument("--odysseus-ratio", type=float, default=1.0, help="Insight ratio bonus")
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
        consensus = ProofOfCoherenceConsensus(consensus_threshold=c["consensus_threshold"])
        # Mock voting state
        consensus.votes[args.fork_id] = [
            ForkVote("vertex-1", True, time.time(), b"sig1", weight=0.85),
            ForkVote("vertex-2", True, time.time(), b"sig2", weight=0.72),
            ForkVote("vertex-3", False, time.time(), b"sig3", weight=0.41),
        ]
        accept, score = consensus.evaluate_merge(args.fork_id, odysseus_insight_ratio=args.odysseus_ratio)
        status = "✅ ACCEPTED" if accept else "❌ REJECTED"
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
