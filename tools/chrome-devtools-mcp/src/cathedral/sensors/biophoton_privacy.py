# src/cathedral/sensors/biophoton_privacy.py
# Módulos de privacidade integrados ao sensor de biophotons

import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class BiophotonFrame:
    timestamp_ns: int
    pixel_data: np.ndarray
    band: np.ndarray

@dataclass
class ZKProofInput:
    spectral_hash: str
    coherence_estimate: float
    metabolic_context_hash: str
    participant_did_hash: str

@dataclass
class ProcessedBiophotonOutput:
    spectral_hash: str
    coherence_estimate: Optional[float]
    zk_proof_input: Optional[ZKProofInput]
    consent_denied: bool
    device_signature: Optional[str] = None
    timestamp_ns: Optional[int] = None

@dataclass
class MinimizedBiophotonData:
    aggregated_counts: np.ndarray
    coherence_estimate: float
    context: Dict[str, bool]

class BiophotonPrivacyEnforcer:
    """Garante que dados de biophotons sejam processados com soberania."""

    def __init__(self, participant_did: str, consent_engine: any):
        self.participant_did = participant_did
        self.consent = consent_engine
        self.device_key = self._load_device_ecdsa_key()

    async def process_frame_with_privacy(
        self,
        raw_frame: BiophotonFrame,
        consent_scope: str,
    ) -> ProcessedBiophotonOutput:
        """Processa frame de biophotons com privacidade por design."""

        # 1. Verificar consentimento antes de qualquer processamento
        consent_check = await self.consent.check_consent(
            scope=consent_scope,
            context="biophoton_capture",
            participant_did=self.participant_did,
        )
        if not consent_check.get("granted", False):
            # Retornar apenas hash de "silêncio" se consentimento negado
            return ProcessedBiophotonOutput(
                spectral_hash=self._compute_silence_hash(),
                coherence_estimate=None,
                zk_proof_input=None,
                consent_denied=True,
            )

        # 2. Aplicar minimização de dados no hardware
        minimized = self._minimize_data_on_device(raw_frame)

        # 3. Computar hash espectral (não reversível)
        spectral_hash = self._poseidon_hash(minimized.aggregated_counts)

        # 4. Preparar input para ZK-proof (sem dados brutos)
        zk_input = ZKProofInput(
            spectral_hash=spectral_hash,
            coherence_estimate=minimized.coherence_estimate,
            metabolic_context_hash=self._hash_metabolic_context(minimized.context),
            participant_did_hash=hashlib.sha256(
                self.participant_did.encode()
            ).hexdigest()[:32],
        )

        # 5. Assinar output com chave do dispositivo (para auditoria)
        signature = self._sign_output(spectral_hash, zk_input, self.device_key)

        return ProcessedBiophotonOutput(
            spectral_hash=spectral_hash,
            coherence_estimate=minimized.coherence_estimate,
            zk_proof_input=zk_input,
            consent_denied=False,
            device_signature=signature,
            timestamp_ns=raw_frame.timestamp_ns,
        )

    def _minimize_data_on_device(self, frame: BiophotonFrame) -> MinimizedBiophotonData:
        """Agrega dados no dispositivo para minimizar informação exposta."""
        # Agregação por banda espectral (reduz 512 pixels → 5 valores)
        bands = ["UV", "blue", "green", "red", "NIR"]
        aggregated = np.array([
            np.mean(frame.pixel_data[frame.band == b]) if np.any(frame.band == b) else 0
            for b in bands
        ])

        # Cálculo preliminar de coerência (heurística simplificada)
        coherence = self._estimate_coherence_heuristic(aggregated)

        # Contexto metabólico resumido (apenas flags binárias)
        context_flags = {
            "high_ros": bool(aggregated[0] > 500),  # UV alto → ROS alto
            "high_atp": bool(aggregated[4] > 800),  # NIR alto → ATP alto
            "stress_pattern": bool(self._detect_stress_pattern(aggregated)),
        }

        return MinimizedBiophotonData(
            aggregated_counts=aggregated,
            coherence_estimate=coherence,
            context=context_flags,
        )

    def _compute_silence_hash(self) -> str:
        """Retorna hash padrão quando consentimento é negado."""
        # Hash de "silêncio luminoso" — não revela se houve captura ou não
        return hashlib.sha256(
            f"biophoton_silence_{self.participant_did}".encode()
        ).hexdigest()

    def _load_device_ecdsa_key(self):
        return "device_private_key_placeholder"

    def _poseidon_hash(self, data: np.ndarray) -> str:
        # Placeholder para o hash Poseidon real
        return hashlib.sha256(data.tobytes()).hexdigest()

    def _hash_metabolic_context(self, context: Dict) -> str:
        return hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()

    def _sign_output(self, spectral_hash: str, zk_input: ZKProofInput, key: str) -> str:
        # Placeholder para assinatura ECDSA
        return "ecdsa_signature_placeholder"

    def _estimate_coherence_heuristic(self, aggregated_counts: np.ndarray) -> float:
        # Heurística simplificada: razão entre bandas NIR/Red e ruído
        return float(np.clip(aggregated_counts[4] / (aggregated_counts[0] + 1), 0, 1))

    def _detect_stress_pattern(self, aggregated_counts: np.ndarray) -> bool:
        # Alta emissão UV/Blue comparada ao baseline
        return aggregated_counts[0] > 700
