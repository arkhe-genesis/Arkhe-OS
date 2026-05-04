#!/usr/bin/env python3
# src/federation/federated_survey_protocol.py
import json
import hashlib
import asyncio
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

class SurveyType(Enum):
    DESI = "desi"
    PLANCK = "planck"
    LSST = "lsst"
    EUCLID = "euclid"
    JWST = "jwst"
    CMB_S4 = "cmb_s4"
    SKA = "ska"
    CUSTOM = "custom"

class ProofStatus(Enum):
    GENERATED = "generated"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

@dataclass
class CosmicParameterProof:
    proof_id: str
    survey_type: SurveyType
    survey_instance_id: str
    parameter_name: str
    parameter_value_scaled: int
    proof_data: Dict
    nullifier: str
    timestamp: int
    status: ProofStatus = ProofStatus.GENERATED
    consensus_weight: float = 1.0

class FederatedSurveyNode:
    def __init__(self, survey_type: SurveyType, instance_id: str):
        self.survey_type = survey_type
        self.instance_id = instance_id
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        self.pending_proofs: Dict[str, CosmicParameterProof] = {}

    def generate_parameter_proof(self, parameter_name: str, value: float) -> CosmicParameterProof:
        scaling = 10**120
        value_scaled = int(value * scaling)
        proof_id = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
        nullifier = hashlib.sha256(f"{self.instance_id}_{proof_id}".encode()).hexdigest()

        proof = CosmicParameterProof(
            proof_id=proof_id,
            survey_type=self.survey_type,
            survey_instance_id=self.instance_id,
            parameter_name=parameter_name,
            parameter_value_scaled=value_scaled,
            proof_data={"pi_a": [], "pi_b": [], "pi_c": []}, # Mock ZK data
            nullifier=nullifier,
            timestamp=int(asyncio.get_event_loop().time() * 1e9)
        )
        self.pending_proofs[proof_id] = proof
        return proof

    def sign_message(self, message: bytes) -> bytes:
        return self.private_key.sign(message, ec.ECDSA(hashes.SHA256()))

class FederationHub:
    def __init__(self):
        self.proofs: List[CosmicParameterProof] = []

    def receive_proof(self, proof: CosmicParameterProof):
        self.proofs.append(proof)
        print(f"Hub: Recebida prova {proof.proof_id} de {proof.survey_instance_id}")

    def calculate_consensus(self) -> float:
        if not self.proofs: return 0.0
        values = [p.parameter_value_scaled for p in self.proofs]
        return float(np.mean(values))
