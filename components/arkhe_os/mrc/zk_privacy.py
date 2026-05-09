from enum import Enum
from dataclasses import dataclass
import numpy as np
import hashlib
import random
from typing import List, Dict
from datetime import datetime
from arkhe_os.mrc.qhttp_bridge import QHTTPOverMRCBridge, QHTTPMessage, QHTTPMessageType

class ZKProofType(Enum):
    GRADIENT_RANGE = "gradient_range"
    GRADIENT_NORM = "gradient_norm"
    UPDATE_CONSISTENCY = "update_consistency"
    COHERENCE_MEMBERSHIP = "coherence_membership"

@dataclass
class ZKProof:
    proof_type: ZKProofType
    commitment: np.ndarray
    challenge: np.ndarray
    response: np.ndarray
    public_inputs: Dict
    verified: bool = False

class MRCZKPrivacyLayer:
    def __init__(self, node_id: str, qhttp_bridge: QHTTPOverMRCBridge):
        self.node_id = node_id
        self.qhttp = qhttp_bridge
        self.proof_history: List[ZKProof] = []
        self.verification_cache: Dict[str, bool] = {}
        self.fhe_params = {'modulus': 2**32, 'noise_budget': 100, 'scale': 2**20}

    def _hash_commitment(self, value: np.ndarray, blinding: int) -> np.ndarray:
        combined = np.concatenate([value.flatten(), np.array([blinding])])
        return np.array([int(hashlib.sha256(combined.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']])

    def prove_gradient_range(self, gradient: np.ndarray, min_val: float, max_val: float) -> ZKProof:
        blinding = random.randint(1, self.fhe_params['modulus'] - 1)
        commitment = self._hash_commitment(gradient, blinding)
        all_in_range = np.all((gradient >= min_val) & (gradient <= max_val))

        challenge_input = np.concatenate([commitment, np.array([min_val, max_val])])
        challenge = int(hashlib.sha256(challenge_input.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']

        response = (blinding + challenge * int(np.sum(gradient) * self.fhe_params['scale'])) % self.fhe_params['modulus']

        proof = ZKProof(
            proof_type=ZKProofType.GRADIENT_RANGE,
            commitment=commitment,
            challenge=np.array([challenge]),
            response=np.array([response]),
            public_inputs={
                'min_val': min_val,
                'max_val': max_val,
                'gradient_shape': gradient.shape,
                'gradient_dtype': str(gradient.dtype),
                'actual_in_range': all_in_range
            },
            verified=all_in_range
        )
        self.proof_history.append(proof)
        return proof

    def prove_gradient_norm(self, gradient: np.ndarray, target_norm: float, tolerance: float = 0.01) -> ZKProof:
        actual_norm = np.linalg.norm(gradient)
        in_tolerance = abs(actual_norm - target_norm) <= tolerance * target_norm

        blinding = random.randint(1, self.fhe_params['modulus'] - 1)
        commitment = self._hash_commitment(gradient, blinding)

        challenge_input = np.concatenate([commitment, np.array([target_norm, tolerance])])
        challenge = int(hashlib.sha256(challenge_input.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']

        response = (blinding + challenge * int(actual_norm * self.fhe_params['scale'])) % self.fhe_params['modulus']

        proof = ZKProof(
            proof_type=ZKProofType.GRADIENT_NORM,
            commitment=commitment,
            challenge=np.array([challenge]),
            response=np.array([response]),
            public_inputs={
                'target_norm': target_norm,
                'tolerance': tolerance,
                'gradient_shape': gradient.shape,
                'actual_norm': actual_norm,
                'verified': in_tolerance
            },
            verified=in_tolerance
        )
        self.proof_history.append(proof)
        return proof

    def verify_proof(self, proof: ZKProof, prover_node: str) -> bool:
        proof_id = f"{prover_node}_{proof.proof_type.value}_{hash(proof.commitment.tobytes())}"
        if proof_id in self.verification_cache:
            return self.verification_cache[proof_id]

        if proof.proof_type == ZKProofType.GRADIENT_RANGE:
            expected_input = np.concatenate([proof.commitment, np.array([proof.public_inputs['min_val'], proof.public_inputs['max_val']])])
        elif proof.proof_type == ZKProofType.GRADIENT_NORM:
            expected_input = np.concatenate([proof.commitment, np.array([proof.public_inputs['target_norm'], proof.public_inputs['tolerance']])])
        else:
            self.verification_cache[proof_id] = False
            return False

        expected_challenge = int(hashlib.sha256(expected_input.tobytes()).hexdigest(), 16) % self.fhe_params['modulus']
        is_valid = (proof.challenge[0] == expected_challenge) and proof.verified

        self.verification_cache[proof_id] = is_valid
        return is_valid

    def send_verified_gradient(self, gradient: np.ndarray, dest_node: str, proof: ZKProof) -> Dict:
        combined = np.concatenate([
            np.array([proof.challenge[0], proof.response[0], proof.commitment[0], 1.0 if proof.verified else 0.0]),
            gradient.flatten()[:100]
        ])
        msg = QHTTPMessage(
            msg_id=f"zk_grad_{random.randint(0, 999999)}",
            msg_type=QHTTPMessageType.GRADIENT_SLICE,
            src_node=self.node_id,
            dest_node=dest_node,
            payload=combined,
            coherence_signature=0.6,
            timestamp=datetime.now().timestamp(),
            priority=2
        )
        return self.qhttp.send_qhttp_message(msg)

    def get_privacy_stats(self) -> Dict:
        by_type = {}
        for p in self.proof_history:
            by_type[p.proof_type.value] = by_type.get(p.proof_type.value, 0) + 1
        return {
            'node_id': self.node_id,
            'total_proofs_generated': len(self.proof_history),
            'proofs_by_type': by_type,
            'verified_proofs': sum(1 for p in self.proof_history if p.verified),
            'verification_cache_size': len(self.verification_cache)
        }
