import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

@dataclass
class FederatedAuditProof:
    """Aggregated proof for cross-repo audit verification."""
    proof_id: str
    participating_repos: List[str]
    individual_proofs: Dict[str, str]  # repo_id → Zinc+ proof (hex)
    aggregated_proof: str  # Composed Zinc+ proof
    public_inputs: Dict[str, Dict]  # repo_id → {threshold, domain, timestamp}
    verification_key_hash: str
    timestamp: float

class FederatedAuditVerifier:
    """Verify cross-repo audits without sharing sensitive code — Substrato 259."""

    def __init__(self, zinc_plus_verifier: Callable):
        self.zinc_verify = zinc_plus_verifier
        self.verification_log: List[Dict] = []

    def compose_proofs(self, individual_proofs: Dict[str, Dict]) -> FederatedAuditProof:
        """Compose multiple Zinc+ proofs into a single federated proof."""
        # In production: use Zinc+ composition API
        # This is a simplified placeholder
        proof_id = hashlib.sha256(
            json.dumps(individual_proofs, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Aggregate public inputs
        public_inputs = {
            repo_id: {
                'threshold': proof_data['threshold'],
                'domain': proof_data['domain'],
                'timestamp': proof_data['timestamp']
            }
            for repo_id, proof_data in individual_proofs.items()
        }

        # Placeholder for actual proof composition
        aggregated = hashlib.sha256(
            ''.join(proof['proof_hex'] for proof in individual_proofs.values()).encode()
        ).hexdigest()

        return FederatedAuditProof(
            proof_id=proof_id,
            participating_repos=list(individual_proofs.keys()),
            individual_proofs={rid: p['proof_hex'] for rid, p in individual_proofs.items()},
            aggregated_proof=aggregated,
            public_inputs=public_inputs,
            verification_key_hash="vk_federated_v1",
            timestamp=datetime.now().timestamp()
        )

    def verify_federated_proof(self, federated_proof: FederatedAuditProof) -> Dict:
        """Verify the aggregated proof and individual components."""
        results = {}

        # Verify each individual proof first
        for repo_id, proof_hex in federated_proof.individual_proofs.items():
            public_input = federated_proof.public_inputs[repo_id]
            # In production: call Zinc+ verifier with actual public inputs
            individual_valid = self.zinc_verify(
                proof=proof_hex,
                public_inputs=public_input,
                vk_hash=federated_proof.verification_key_hash
            )
            results[repo_id] = {
                'individual_valid': individual_valid,
                'threshold': public_input['threshold'],
                'domain': public_input['domain']
            }

        # Verify aggregated proof (ensures composition correctness)
        aggregated_valid = self.zinc_verify(
            proof=federated_proof.aggregated_proof,
            public_inputs={
                'repos': federated_proof.participating_repos,
                'verification_key': federated_proof.verification_key_hash,
                'timestamp': federated_proof.timestamp
            },
            vk_hash=federated_proof.verification_key_hash + "_composed"
        )

        # Overall validity: all individual + aggregated must pass
        all_individual_valid = all(r['individual_valid'] for r in results.values())
        overall_valid = all_individual_valid and aggregated_valid

        self.verification_log.append({
            'proof_id': federated_proof.proof_id,
            'timestamp': datetime.now().timestamp(),
            'overall_valid': overall_valid,
            'individual_results': results,
            'aggregated_valid': aggregated_valid
        })

        return {
            'valid': overall_valid,
            'proof_id': federated_proof.proof_id,
            'participating_repos': federated_proof.participating_repos,
            'individual_validity': {rid: r['individual_valid'] for rid, r in results.items()},
            'verification_time_ms': 0,  # Placeholder
            'log_entry': len(self.verification_log)
        }

    def generate_audit_report(self, federated_proof: FederatedAuditProof) -> Dict:
        """Generate human-readable audit report from verified proof."""
        verification = self.verify_federated_proof(federated_proof)

        return {
            'report_id': f"audit_report_{federated_proof.proof_id}",
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'PASS' if verification['valid'] else 'FAIL',
            'participating_repos': federated_proof.participating_repos,
            'repo_details': [
                {
                    'repo_id': repo_id,
                    'domain': federated_proof.public_inputs[repo_id]['domain'],
                    'threshold': federated_proof.public_inputs[repo_id]['threshold'],
                    'verified': verification['individual_validity'].get(repo_id, False)
                }
                for repo_id in federated_proof.participating_repos
            ],
            'proof_metadata': {
                'proof_id': federated_proof.proof_id,
                'verification_key': federated_proof.verification_key_hash,
                'composed_proof_size_bytes': len(federated_proof.aggregated_proof) // 2  # hex → bytes
            },
            'verification_log_index': len(self.verification_log) - 1
        }
