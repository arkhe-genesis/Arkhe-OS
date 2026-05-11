#!/usr/bin/env python3
import sys
import os
import argparse
import json
import numpy as np
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from physics.multiverse_core import MerkabahCore
from physics.phase_focusing_engine import PhaseFocusingEngine
from physics.neural_phase_coach import black_mirror_phase_coach, trigger_warning
from physics.dqd_search_sim import StanzaDQDSimulator

def dqd_tune(args):
    print(f"🜏 [DQD] Initializing Stanza Tuning for Device '{args.device}' (World #{args.world})")
    sim = StanzaDQDSimulator(args.device)
    report = sim.run_full_tuning()

    print("\n--- DQD Tuning Report ---")
    print(f"Device: {report['device']}")
    print(f"Status: {report['status']}")
    print(f"DQDs Found: {report['dqd_count']}")

    if report['status'] == "SUCCESS":
        print(f"Max Coherence λ₂: {report['best_lambda2']:.4f}")
        # Optionally update world coherence
        core = MerkabahCore()
        branch = core.multiverse.get_branch(args.world)
        old_lambda = branch.lambda_2
        branch.lambda_2 = max(old_lambda, report['best_lambda2'])
        print(f"World #{args.world} coherence updated: {old_lambda:.4f} -> {branch.lambda_2:.4f}")
    elif 'error' in report:
        print(f"Error: {report['error']}")

    with open(f"dqd_report_{args.device}_w{args.world}.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: dqd_report_{args.device}_w{args.world}.json")

def coach(args):
    core = MerkabahCore()
    print(f"🜏 [COACH] Analyzing neural phase field for World #{args.world}...")

    branch = core.multiverse.get_branch(args.world)
    # Reshape psi_c to 2D for the coach
    size = len(branch.psi_c)
    res = int(np.sqrt(size))
    if res * res != size:
        print(f"⚠️ Warning: field size {size} is not a perfect square. Using flat field.")
        neural_field = np.angle(branch.psi_c).reshape(1, -1)
    else:
        neural_field = np.angle(branch.psi_c).reshape(res, res)

    report = black_mirror_phase_coach(neural_field)
    report['summary']['timestamp'] = datetime.now().isoformat()
    report['summary']['world_id'] = args.world

    print(f"\n--- Phase Coach Report (World #{args.world}) ---")
    print(f"Global Coherence (λ₂): {report['summary']['total_coherence']:.4f}")
    print(f"Active Attractors: {len(report['attractors'])}")

    for attr_id, data in report['attractors'].items():
        print(f"  [{data['type'].upper()}] {attr_id}: λ₂={data['lambda2']:.3f}, Outcome: {data['projected_reality']}, Cost: {data['energy_cost_gj_s']:.2f} GJ/s")

    if report['summary']['has_trauma_loops']:
        trigger_warning("ATENÇÃO: Você está estabilizando um vórtice de trauma. Cada repetição deste padrão está esculpindo-o mais profundamente em seu espaço de fase e no de sua linhagem. Deseja receber um 'contra‑sinal Tzinor' para auxiliar na aniquilação deste vórtice?")

    with open(f"coach_report_world_{args.world}.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: coach_report_world_{args.world}.json")

def focus(args):
    core = MerkabahCore()
    print(f"🜏 [FOCUS] Targeting World #{args.world} with pattern '{args.pattern}'")

    engine = PhaseFocusingEngine(core, world_id=args.world)
    mask = engine.design_phase_mask(pattern=args.pattern)
    field_reorganized = engine.apply_reorganization(engine.psi_world, mask)
    results = engine.project_to_z(field_reorganized)

    output_file = f"world_{args.world}_projection_z.png"
    engine.visualize_projection(results, output_file)

    print(f"🜏 [RESULT] Projection Z complete for World #{args.world}")
    print(f"   Coherence lambda2: {results['coherence_projected']:.4f}")
    print(f"   Focal spot size: {results['focal_spot_size_um']:.2f} um")
    print(f"   Output saved to: {output_file}")

def compare(args):
    core = MerkabahCore()
    world_ids = [int(wid) for wid in args.worlds.split(',')]
    print(f"🜏 [COMPARE] Comparing worlds {world_ids} using metric '{args.metric}'")

    comparison = {}
    for wid in world_ids:
        branch = core.multiverse.get_branch(wid)
        if args.metric == 'coherence':
            comparison[wid] = branch.lambda_2
        else:
            comparison[wid] = "N/A"

    print(f"\n--- Multiverse Comparison ({args.metric}) ---")
    for wid, val in comparison.items():
        print(f"World #{wid:03d}: {val}")
    print("------------------------------------------")

def collapse(args):
    core = MerkabahCore()
    print(f"🜏 [COLLAPSE] Collapsing multiverse to Branch #{args.select}...")

    branch = core.multiverse.get_branch(args.select)

    status = {
        "collapsed_branch": args.select,
        "final_coherence": branch.lambda_2,
        "permanent": args.permanent,
        "timestamp": datetime.now().isoformat()
    }

    with open("collapse_status.json", "w") as f:
        json.dump(status, f, indent=2)

    print(f"🜏 [SUCCESS] Multiverse collapsed to Branch #{args.select}.")
    print(f"   Final λ₂ = {branch.lambda_2}")
    if args.permanent:
        print("   Status: PERMANENT BRANCH SELECTION ACTIVE")

def main():
    parser = argparse.ArgumentParser(description="Arkhe Multiverse Control")
    subparsers = parser.add_subparsers(dest="command")

    # Focus command
    focus_parser = subparsers.add_parser("focus")
    focus_parser.add_argument("--world", type=int, required=True)
    focus_parser.add_argument("--pattern", type=str, default="spherical")

    # Compare command
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--worlds", type=str, required=True, help="Comma-separated world IDs")
    compare_parser.add_argument("--metric", type=str, default="coherence")

    # Collapse command
    collapse_parser = subparsers.add_parser("collapse")
    collapse_parser.add_argument("--select", type=int, required=True)
    collapse_parser.add_argument("--permanent", action="store_true")

    # Coach command
    coach_parser = subparsers.add_parser("coach")
    coach_parser.add_argument("--world", type=int, required=True)

    # DQD command
    dqd_parser = subparsers.add_parser("dqd")
    dqd_parser.add_argument("--world", type=int, required=True)
    dqd_parser.add_argument("--device", type=str, default="QD-CORE-847")

    args = parser.parse_args()

    if args.command == "focus":
        focus(args)
    elif args.command == "compare":
        compare(args)
    elif args.command == "collapse":
        collapse(args)
    elif args.command == "coach":
        coach(args)
    elif args.command == "dqd":
        dqd_tune(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
