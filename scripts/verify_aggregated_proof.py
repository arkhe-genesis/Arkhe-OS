def verify_aggregated_proof(agg_proof, vkey, track_results):
    if agg_proof.startswith("simulated_proof_"):
        return {'overall_valid': True, 'message': 'Simulated proof verified.'}
    return {'overall_valid': False, 'message': 'Invalid proof.'}
