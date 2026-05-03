import sys
import os

# Ensure we can import from core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.protocol.fork.ledger_temporal_fork_protocol import LedgerTemporalForkProtocol, LedgerState

def simulate_timeline_branching():
    print("⏳ Starting Substrate 126 Ledger Temporal Forking Simulation")
    print("=" * 60)

    # 1. Initialize Protocol
    protocol = LedgerTemporalForkProtocol(main_chain_root=b"genesis", consensus_threshold=0.03)

    # Give some historical fidelity to vertices
    protocol.update_vertex_fidelity("vertex_1", 1.5)
    protocol.update_vertex_fidelity("vertex_2", 1.2)
    protocol.update_vertex_fidelity("vertex_3", 0.9)

    # 2. Build Synthetic Main Chain
    print("\n🌿 Building Main Chain...")
    for i in range(1, 6):
        ts = float(i)
        state = LedgerState(
            logical_timestamp=ts,
            merkle_root=f"root_{i}".encode(),
            face_hashes=[f"face_{i}".encode()],
            vertex_signatures={"vertex_1": b"sig", "vertex_2": b"sig", "vertex_3": b"sig"},
            epsilon_stats={"mean": 0.0472 + (i * 0.01)}, # Starts at perfect 0.0472, drifts slightly
            uniphics_stats={"k": 0.0472, "E_d": 1.0},
            odysseus_insight=0.0
        )
        protocol.main_chain[ts] = state
        print(f"  Added state at ts={ts}, ε={state.epsilon_stats['mean']:.4f}")

    print(f"\nMain chain tip at ts=5.0 with ε={protocol.main_chain[5.0].epsilon_stats['mean']:.4f}")

    # 3. Create a Fork
    fork_ts = 3.0
    print(f"\n🔀 Creating temporal fork at ts={fork_ts} (Reason: test_super_linear_gain)")
    fork_id = protocol.fork_at(fork_ts, reason="test_super_linear_gain")
    print(f"  Fork ID generated: {fork_id}")

    # 4. Simulate Diverging Evolution on Fork
    print("\n🌱 Simulating Fork Evolution...")
    for i in range(4, 7):
        ts = float(i)
        # Fork stays closer to the ideal 0.0472 or 0.07 depending on the scoring
        # Let's make the fork achieve a highly optimized ε of 0.07 (perfect base score)
        # and gain significant Odysseus insight.
        state = LedgerState(
            logical_timestamp=ts,
            merkle_root=f"fork_root_{i}".encode(),
            face_hashes=[f"fork_face_{i}".encode()],
            vertex_signatures={"vertex_1": b"sig", "vertex_2": b"sig", "vertex_3": b"sig"},
            epsilon_stats={"mean": 0.07}, # Ideal for the base score `1.0 - abs(ε - 0.07) / 0.03`
            uniphics_stats={"k": 0.0472, "E_d": 0.5}, # Faster Uniphics flow
            odysseus_insight=(i - 3) * 0.05 # Super-linear gain increases over time
        )
        protocol.append_to_fork(fork_id, state)
        print(f"  Appended state to fork at ts={ts}, ε={state.epsilon_stats['mean']:.4f}, Odysseus={state.odysseus_insight:.4f}")

    # 5. Evaluate Coherence
    print("\n⚖️ Evaluating Consensus Epsilon Merge...")
    coherence_gain = protocol.evaluate_fork_coherence(fork_id)
    print(f"  Calculated Coherence Gain: {coherence_gain:.4f}")
    print(f"  Required Consensus Threshold: {protocol.consensus_threshold}")

    # 6. Execute Merge
    print("\n🔄 Executing Merge...")
    success = protocol.merge_fork(fork_id)
    if success:
        print(f"  ✅ Merge Accepted! The fork {fork_id} is now the main chain.")
        new_tip_ts = max(protocol.main_chain.keys())
        new_tip = protocol.main_chain[new_tip_ts]
        print(f"  New main chain tip ts={new_tip_ts}, ε={new_tip.epsilon_stats['mean']:.4f}")
    else:
        print(f"  ❌ Merge Rejected.")

    # 7. Test Rollback
    print(f"\n⏪ Testing Rollback to ts={fork_ts}...")
    protocol.rollback_to(fork_ts)
    tip_ts = max(protocol.main_chain.keys())
    print(f"  Rollback complete. Main chain tip is now ts={tip_ts}")

    print("\n✅ Simulation Complete.")

if __name__ == "__main__":
    simulate_timeline_branching()
