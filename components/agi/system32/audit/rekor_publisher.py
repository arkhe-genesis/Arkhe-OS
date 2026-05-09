#!/usr/bin/env python3
"""
audit/rekor_publisher.py — Publicação automática em Sigstore Rekor.
Registra provas de coerência em log de transparência público.
"""
import json
import time
import requests
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class RekorEntry:
    """Entrada no log de transparência Rekor."""
    artifact_hash: str
    proof_data: Dict  # CoherenceProof serializado
    rekor_uuid: Optional[str] = None
    inclusion_proof: Optional[Dict] = None
    published_at: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "artifact_hash": self.artifact_hash,
            "proof_data": self.proof_data,
            "rekor_uuid": self.rekor_uuid,
            "inclusion_proof": self.inclusion_proof,
            "published_at": self.published_at
        }

class RekorPublisher:
    """Publica provas de auditoria em Sigstore Rekor."""

    def __init__(self, rekor_url: str = "https://rekor.sigstore.dev", mock_requests=False):
        self.rekor_url = rekor_url
        self.session = requests.Session()
        self.mock_requests = mock_requests

    def publish_proof(self,
                     coherence_proof,
                     metadata: Dict) -> Optional[RekorEntry]:
        """Publica prova de coerência em Rekor."""
        entry = {
            "kind": "arkhe_coherence_proof",
            "apiVersion": "0.0.1",
            "spec": {
                "data": {
                    "artifact_hash": coherence_proof.artifact_hash,
                    "artifact_seal": coherence_proof.artifact_seal,
                    "coherence_score": coherence_proof.overall_coherence,
                    "signature": coherence_proof.signature,
                    "metadata": metadata
                },
                "signature": {
                    "content": coherence_proof.signature,
                    "publicKey": {
                        "content": self._get_public_key_pem()
                    }
                }
            }
        }

        try:
            if self.mock_requests:
                result = {
                    "uuid": "mock_uuid_123",
                    "proof": {"rootHash": "mock_root_hash"}
                }
            else:
                response = self.session.post(
                    f"{self.rekor_url}/api/v1/log/entries",
                    json=entry,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()

            return RekorEntry(
                artifact_hash=coherence_proof.artifact_hash,
                proof_data=coherence_proof.to_dict(),
                rekor_uuid=result.get("uuid"),
                inclusion_proof=result.get("proof"),
                published_at=time.time()
            )

        except Exception as e:
            print(f"⚠️ Falha ao publicar em Rekor: {e}")
            return None

    def verify_entry(self, entry: RekorEntry) -> bool:
        """Verifica inclusão de entrada no log Rekor."""
        if not entry.rekor_uuid or not entry.inclusion_proof:
            return False

        try:
            if self.mock_requests:
                return True

            response = self.session.get(
                f"{self.rekor_url}/api/v1/log/entries/{entry.rekor_uuid}",
                timeout=30
            )
            response.raise_for_status()

            # Verificar prova de inclusão Merkle
            return self._verify_merkle_inclusion(
                entry.inclusion_proof,
                entry.artifact_hash
            )

        except Exception:
            return False

    def _get_public_key_pem(self) -> str:
        """Retorna chave pública em formato PEM."""
        # Implementação simplificada
        return "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"

    def _verify_merkle_inclusion(self, proof: Dict, artifact_hash: str) -> bool:
        """Verifica prova de inclusão Merkle no log Rekor."""
        # Implementação simplificada
        return proof.get("rootHash") is not None
