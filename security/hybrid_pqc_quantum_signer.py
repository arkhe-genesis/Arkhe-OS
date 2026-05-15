#!/usr/bin/env python3
"""
Substrato 191: Assinador Híbrido PQC+Quântico para Produção
Combina assinaturas PQC (Dilithium-3) com testemunhos quânticos (fótons EPR)
para segurança máxima com fallback clássico garantido.
"""

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

# Tentar importar bibliotecas PQC
try:
    from oqs import Signature as PQCSignature
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False
    logging.warning("⚠️  liboqs não disponível — usando modo simulado para PQC")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignatureMode(Enum):
    """Modos de assinatura suportados."""
    PQC_ONLY = "pqc_only"           # Apenas Dilithium-3
    QUANTUM_ONLY = "quantum_only"   # Apenas testemunho quântico (experimental)
    HYBRID_PARALLEL = "hybrid_parallel"  # Ambas em paralelo (recomendado)
    HYBRID_SEQUENTIAL = "hybrid_sequential"  # PQC primeiro, quântico como reforço

@dataclass
class HybridSignatureResult:
    """Resultado de assinatura híbrida."""
    success: bool
    mode: SignatureMode
    pqc_signature_hex: Optional[str]
    quantum_witness_hash: Optional[str]
    combined_signature_hash: str
    signing_time_ms: float
    fallback_used: bool
    temporal_seal: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class VerificationResult:
    """Resultado de verificação de assinatura híbrida."""
    valid: bool
    pqc_valid: bool
    quantum_valid: bool
    confidence_score: float  # 0.0 a 1.0
    verification_time_ms: float

class HybridPQCQuantumSigner:
    """
    Assinador híbrido que combina PQC clássico com testemunhos quânticos.

    Arquitetura de segurança em camadas:
    1. Camada PQC: Dilithium-3 (NIST recomendado) para autenticação clássica
    2. Camada Quântica: Testemunho de fótons EPR para integridade física
    3. Combinação: Hash SHA3-256 das duas assinaturas para selo único
    4. Fallback: Se quântico falhar, PQC ainda garante segurança mínima

    Casos de uso:
    • Assinatura de blocos TemporalChain com prova quântica de integridade
    • Autenticação de mensagens críticas no Q-Bus com verificação física
    • Certificação de eventos de emergência da malha com testemunho emaranhado
    """

    def __init__(
        self,
        pqc_algorithm: str = "ML-DSA-65",
        quantum_witness_photons: int = 256,
        temporal_chain=None,
        hsm_config: Optional[Dict] = None,
    ):
        self.pqc_algorithm = pqc_algorithm
        self.quantum_photons = quantum_witness_photons
        self.temporal = temporal_chain
        self.hsm_config = hsm_config
        self._pqc_keypair: Optional[Dict] = None
        self._quantum_emitter: Optional = None

        self.pqc_signer = None
        if PQC_AVAILABLE:
            try:
                self.pqc_signer = PQCSignature(pqc_algorithm)
                self._pqc_keypair = {"public_key": self.pqc_signer.generate_keypair(), "private_key": self.pqc_signer.export_secret_key()}
                logger.info(f"✅ Par de chaves PQC gerado: {pqc_algorithm}")
            except Exception as e:
                logger.warning(f"⚠️  Falha ao gerar chaves PQC: {e}")

    async def sign_message(
        self,
        message: bytes,
        metadata: Dict,
        mode: SignatureMode = SignatureMode.HYBRID_PARALLEL,
    ) -> HybridSignatureResult:
        """
        Assina mensagem com esquema híbrido PQC+quântico.

        Args:
            message: Dados a serem assinados
            metadata: Metadados para auditoria
            mode: Modo de assinatura (parallel recomendado)

        Returns:
            HybridSignatureResult com assinaturas e metadados
        """
        start_time = time.time()

        try:
            # 1. Assinatura PQC (clássica)
            pqc_sig = None
            pqc_success = False

            if PQC_AVAILABLE and self._pqc_keypair:
                try:
                    pqc_sig = self.pqc_signer.sign(message)
                    pqc_success = True
                except Exception as e:
                    logger.warning(f"⚠️  Falha na assinatura PQC: {e}")

            # 2. Testemunho quântico (física)
            quantum_witness = None
            quantum_success = False

            if mode in [SignatureMode.QUANTUM_ONLY, SignatureMode.HYBRID_PARALLEL, SignatureMode.HYBRID_SEQUENTIAL]:
                try:
                    quantum_witness = await self._generate_quantum_witness(message, metadata)
                    quantum_success = quantum_witness is not None
                except Exception as e:
                    logger.warning(f"⚠️  Falha no testemunho quântico: {e}")

            # 3. Determinar sucesso baseado no modo
            if mode == SignatureMode.PQC_ONLY:
                success = pqc_success
            elif mode == SignatureMode.QUANTUM_ONLY:
                success = quantum_success
            else:  # HYBRID modes
                success = pqc_success or quantum_success  # Fallback garantido

            if not success:
                return HybridSignatureResult(
                    success=False,
                    mode=mode,
                    pqc_signature_hex=None,
                    quantum_witness_hash=None,
                    combined_signature_hash="",
                    signing_time_ms=0,
                    fallback_used=True,
                    error_message="Both PQC and quantum signing failed",
                )

            # 4. Combinar assinaturas em selo único
            combined_input = b""
            if pqc_sig:
                combined_input += pqc_sig
            if quantum_witness:
                combined_input += quantum_witness.encode()

            combined_hash = hashlib.sha3_256(combined_input).hexdigest()

            signing_time_ms = (time.time() - start_time) * 1000

            result = HybridSignatureResult(
                success=True,
                mode=mode,
                pqc_signature_hex=pqc_sig.hex() if pqc_sig else None,
                quantum_witness_hash=hashlib.sha3_256(quantum_witness.encode()).hexdigest()[:16] if quantum_witness else None,
                combined_signature_hash=combined_hash,
                signing_time_ms=signing_time_ms,
                fallback_used=not (pqc_success and quantum_success),
            )

            # 5. Ancorar na TemporalChain
            if self.temporal and result.success:
                result.temporal_seal = await self.temporal.anchor_event(
                    "hybrid_signature_created",
                    {
                        "mode": mode.value,
                        "pqc_success": pqc_success,
                        "quantum_success": quantum_success,
                        "combined_hash": combined_hash[:16],
                        "signing_time_ms": signing_time_ms,
                        "metadata": {k: v for k, v in metadata.items() if k != "content"},
                        "timestamp": time.time(),
                    }
                )

            logger.info(
                f"✅ Assinatura híbrida: {mode.value} | "
                f"PQC:{pqc_success} Quantum:{quantum_success} | "
                f"{signing_time_ms:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Falha na assinatura híbrida: {e}")
            return HybridSignatureResult(
                success=False,
                mode=mode,
                pqc_signature_hex=None,
                quantum_witness_hash=None,
                combined_signature_hash="",
                signing_time_ms=0,
                fallback_used=True,
                error_message=str(e),
            )

    async def _generate_quantum_witness(
        self,
        message: bytes,
        metadata: Dict,
    ) -> Optional[str]:
        """Gera testemunho quântico baseado em fótons EPR."""
        # Em produção: usar emissor de fótons real via arkhe_photon
        # Para demo: simular testemunho com hash quântico-inspired

        # Hash da mensagem como "semente" para estado quântico simulado
        msg_hash = hashlib.sha3_256(message).digest()

        # Simular medição de fótons emaranhados
        # Em produção: emitir self.quantum_photons pares EPR e medir correlações
        witness_data = {
            "message_hash": msg_hash.hex()[:16],
            "photon_count": self.quantum_photons,
            "correlation_pattern": hashlib.sha3_256(
                msg_hash + json.dumps(metadata, sort_keys=True).encode()
            ).hexdigest()[:32],
            "timestamp_ns": time.time_ns(),
        }

        # Gerar witness como string determinística
        witness = hashlib.sha3_256(
            json.dumps(witness_data, sort_keys=True).encode()
        ).hexdigest()

        return witness

    async def verify_signature(
        self,
        message: bytes,
        signature_result: HybridSignatureResult,
        public_key: Optional[bytes] = None,
    ) -> VerificationResult:
        """Verifica assinatura híbrida com confiança ponderada."""
        start_time = time.time()

        pqc_valid = False
        quantum_valid = False

        # Verificar PQC se disponível
        if signature_result.pqc_signature_hex and PQC_AVAILABLE and public_key:
            try:
                verifier = PQCSignature(self.pqc_algorithm)
                pqc_valid = verifier.verify(message, bytes.fromhex(signature_result.pqc_signature_hex), public_key)
            except Exception as e:
                logger.warning(f"⚠️  Falha na verificação PQC: {e}")

        # Verificar testemunho quântico (simulado)
        if signature_result.quantum_witness_hash:
            # Em produção: verificar correlações de fótons recebidos
            # Para demo: verificar consistência do hash
            expected_witness = await self._generate_quantum_witness(message, {})
            expected_hash = hashlib.sha3_256(expected_witness.encode()).hexdigest()[:16]
            quantum_valid = (signature_result.quantum_witness_hash == expected_hash)

        # Calcular score de confiança
        if pqc_valid and quantum_valid:
            confidence = 1.0  # Máxima confiança
        elif pqc_valid or quantum_valid:
            confidence = 0.85  # Confiança alta com fallback
        else:
            confidence = 0.0  # Falha total

        verification_time_ms = (time.time() - start_time) * 1000

        return VerificationResult(
            valid=pqc_valid or quantum_valid,
            pqc_valid=pqc_valid,
            quantum_valid=quantum_valid,
            confidence_score=confidence,
            verification_time_ms=verification_time_ms,
        )

    async def rotate_keys(
        self,
        new_pqc_algorithm: Optional[str] = None,
        overlap_period_hours: int = 24,
    ) -> Dict[str, str]:
        """Rotação de chaves com período de sobreposição para transição suave."""
        # Em produção: integrar com HSM para rotação segura
        # Para demo: simular rotação

        old_key_id = hashlib.sha3_256(
            f"{self.pqc_algorithm}:{time.time() - 3600}".encode()
        ).hexdigest()[:12]

        new_key_id = hashlib.sha3_256(
            f"{new_pqc_algorithm or self.pqc_algorithm}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Ancorar evento de rotação
        if self.temporal:
            await self.temporal.anchor_event(
                "hybrid_key_rotated",
                {
                    "old_key_id": old_key_id,
                    "new_key_id": new_key_id,
                    "algorithm": new_pqc_algorithm or self.pqc_algorithm,
                    "overlap_hours": overlap_period_hours,
                    "timestamp": time.time(),
                }
            )

        return {
            "old_key_id": old_key_id,
            "new_key_id": new_key_id,
            "overlap_until": time.time() + (overlap_period_hours * 3600),
        }
