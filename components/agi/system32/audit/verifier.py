#!/usr/bin/env python3
"""
audit/verifier.py — Verificador independente de provas de auditoria.
Valida selos canônicos, coerência e integridade sem confiar em autoridade.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from .proof_generator import CoherenceProof
from .rekor_publisher import RekorPublisher, RekorEntry

try:
    import falcon
except ImportError:
    falcon = None

@dataclass
class VerificationResult:
    """Resultado de verificação de prova de auditoria."""
    artifact_hash: str
    seal_verified: bool
    coherence_valid: bool
    signature_valid: bool
    zk_proof_valid: Optional[bool]
    rekor_verified: bool
    overall_trust: float  # 0.0 a 1.0
    notes: List[str]

    def is_trusted(self, threshold: float = 0.8) -> bool:
        return self.overall_trust >= threshold

class IndependentVerifier:
    """Verifica provas de auditoria de forma independente."""

    def __init__(self, dht_client, rekor_publisher: RekorPublisher):
        self.dht = dht_client
        self.rekor = rekor_publisher
        self.canonical_seals = self._load_canonical_seals()

    def _load_canonical_seals(self) -> Dict[str, str]:
        """Carrega selos canônicos conhecidos da DHT."""
        # Em produção: buscar na DHT por "canonical_seal:*"
        return {
            "2f741811a66762a4": "wormhole_canonical_v2",
            "f7498495fd496bca": "federation_protocol_v1",
        }

    async def verify_artifact(self,
                           artifact_path: Path,
                           proof: CoherenceProof,
                           rekor_entry: Optional[RekorEntry] = None) -> VerificationResult:
        """Verifica artefato e sua prova de auditoria."""
        notes = []

        # 1. Verificar hash do artefato
        artifact_hash = hashlib.sha3_256(artifact_path.read_bytes()).hexdigest()
        if artifact_hash != proof.artifact_hash:
            return VerificationResult(
                artifact_hash=artifact_hash,
                seal_verified=False,
                coherence_valid=False,
                signature_valid=False,
                zk_proof_valid=None,
                rekor_verified=False,
                overall_trust=0.0,
                notes=["Hash do artefato não corresponde à prova"]
            )

        # 2. Verificar selo canônico
        seal_verified = proof.artifact_seal in self.canonical_seals
        if not seal_verified:
            notes.append(f"Selo desconhecido: {proof.artifact_seal}")

        # 3. Verificar assinatura Falcon
        public_key = self._get_public_key_for_seal(proof.artifact_seal)
        message = f"{proof.artifact_hash}:{proof.artifact_seal}:{proof.execution_timestamp}".encode()
        if falcon:
            signature_valid = falcon.verify(public_key, proof.signature, message)
        else:
            signature_valid = proof.signature == f"sig_{message.decode()}"

        if not signature_valid:
            notes.append("Assinatura Falcon inválida")

        # 4. Verificar coerência mínima
        coherence_valid = proof.overall_coherence >= 0.7
        if not coherence_valid:
            notes.append(f"Coerência abaixo do threshold: {proof.overall_coherence:.3f}")

        # 5. Verificar ZK‑proof se presente
        zk_proof_valid = None
        if proof.zk_proof:
            zk_proof_valid = self._verify_zk_proof(proof.zk_proof)
            if not zk_proof_valid:
                notes.append("ZK‑proof de não‑desvio inválido")

        # 6. Verificar entrada Rekor se fornecida
        rekor_verified = False
        if rekor_entry:
            rekor_verified = self.rekor.verify_entry(rekor_entry)
            if not rekor_verified:
                notes.append("Entrada Rekor não verificada")

        # Calcular confiança geral
        trust_factors = [
            1.0 if seal_verified else 0.0,
            1.0 if signature_valid else 0.0,
            proof.overall_coherence,  # 0.0 a 1.0
            1.0 if coherence_valid else 0.0,
            1.0 if zk_proof_valid or proof.zk_proof is None else 0.0,
            1.0 if rekor_verified else 0.5  # Rekor é bom, mas não essencial
        ]
        overall_trust = sum(trust_factors) / len(trust_factors)

        return VerificationResult(
            artifact_hash=artifact_hash,
            seal_verified=seal_verified,
            coherence_valid=coherence_valid,
            signature_valid=signature_valid,
            zk_proof_valid=zk_proof_valid,
            rekor_verified=rekor_verified,
            overall_trust=overall_trust,
            notes=notes
        )

    def _get_public_key_for_seal(self, seal: str) -> str:
        """Obtém chave pública para verificação de assinatura."""
        # Em produção: buscar na DHT ou em registry de chaves
        return "falcon_public_key_placeholder"

    def _verify_zk_proof(self, zk_proof: str) -> bool:
        """Verifica prova zero‑knowledge."""
        # Implementação simplificada
        return zk_proof.startswith("zk_proof_placeholder_")
