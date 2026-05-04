import hashlib
import json

def aggregate_track_proofs(track_results):
    data_str = json.dumps({k: v['public_outputs'] for k, v in track_results.items()}, sort_keys=True)
    root_hash = hashlib.sha256(data_str.encode()).hexdigest()

    # Optional: extract proofs from instructions to aggregate
    proofs = [v['instruction'].proof.hash for k, v in track_results.items() if hasattr(v['instruction'], 'proof')]

    agg_proof = "simulated_proof_" + root_hash + "_" + "_".join(proofs)
    vkey = "vkey_123"
    return root_hash, agg_proof, vkey
