#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pqc_crypto_adapter.py — Substrato 9029: Adaptador de Criptografia Pós-Quântica
Implementa algoritmos resistentes a ataques quânticos (CRYSTALS-Dilithium, Kyber, SPHINCS+)
com fallback para algoritmos clássicos durante transição.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Tuple
from enum import Enum, auto
import logging

# Tentar importar biblioteca PQC (liboqs ou similar)
try:
    from oqs import Signature, KeyEncapsulation
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False
    logging.warning("⚠️  liboqs não disponível — usando modo simulado para PQC")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class PQCAlgorithm(Enum):
    """Algoritmos pós-quânticos suportados."""
    # Assinatura digital
    DILITHIUM_2 = "CRYSTALS-Dilithium2"
    DILITHIUM_3 = "CRYSTALS-Dilithium3"
    DILITHIUM_5 = "CRYSTALS-Dilithium5"
    SPHINCS_PLUS_SHA2_128f = "SPHINCS+-SHA2-128f-simple"

    # Encriptação/KEM
    KYBER_512 = "CRYSTALS-Kyber512"
    KYBER_768 = "CRYSTALS-Kyber768"
    KYBER_1024 = "CRYSTALS-Kyber1024"

    # Clássico (fallback)
    RSA_4096 = "RSA-4096"
    ECDSA_P384 = "ECDSA-P384"

@dataclass
class CryptoConfig:
    """Configuração para operações criptográficas."""
    primary_algorithm: PQCAlgorithm = PQCAlgorithm.DILITHIUM_3
    fallback_algorithm: PQCAlgorithm = PQCAlgorithm.RSA_4096
    hybrid_mode: bool = True  # Usar combinação PQC + clássico
    key_rotation_days: int = 365
    security_level: int = 3  # 1-5, onde 5 é máximo

@dataclass
class CryptoOperationResult:
    """Resultado de operação criptográfica."""
    success: bool
    algorithm_used: str
    signature_or_ciphertext: Optional[bytes] = None
    verification_result: Optional[bool] = None
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    pqc_fallback_used: bool = False

# ============================================================================
# ADAPTADOR PQC
# ============================================================================

class PQCCryptoAdapter:
    """
    Adaptador unificado para criptografia pós-quântica e clássica.

    Funcionalidades:
    • Assinatura digital com algoritmos PQC (Dilithium, SPHINCS+)
    • Encriptação/KEM com algoritmos PQC (Kyber)
    • Modo híbrido: combinação PQC + clássico para segurança em camadas
    • Fallback automático para algoritmos clássicos se PQC indisponível
    • Rotação automática de chaves com ancoragem temporal
    • Geração de provas de integridade para auditoria
    """

    # Mapeamento de algoritmos para parâmetros NIST
    ALGORITHM_PARAMS = {
        PQCAlgorithm.DILITHIUM_2: {"security_level": 1, "type": "signature"},
        PQCAlgorithm.DILITHIUM_3: {"security_level": 3, "type": "signature"},
        PQCAlgorithm.DILITHIUM_5: {"security_level": 5, "type": "signature"},
        PQCAlgorithm.SPHINCS_PLUS_SHA2_128f: {"security_level": 1, "type": "signature"},
        PQCAlgorithm.KYBER_512: {"security_level": 1, "type": "kem"},
        PQCAlgorithm.KYBER_768: {"security_level": 3, "type": "kem"},
        PQCAlgorithm.KYBER_1024: {"security_level": 5, "type": "kem"},
    }

    def __init__(self, config: CryptoConfig = None):
        self.config = config or CryptoConfig()
        self._keys: Dict[str, Dict] = {}  # Cache de chaves
        self._pqc_available = PQC_AVAILABLE

        if not self._pqc_available:
            logger.warning("⚠️  Executando em modo simulado — liboqs não instalado")

    def generate_keypair(self, algorithm: Optional[PQCAlgorithm] = None) -> Dict[str, bytes]:
        """Gera par de chaves para algoritmo especificado."""
        algorithm = algorithm or self.config.primary_algorithm

        if self._pqc_available and algorithm in self.ALGORITHM_PARAMS:
            params = self.ALGORITHM_PARAMS[algorithm]

            if params["type"] == "signature":
                signer = Signature(algorithm.value)
                public_key = signer.generate_keypair()
                return {
                    "public_key": signer.public_key,
                    "private_key": signer.secret_key,
                    "algorithm": algorithm.value,
                    "type": "signature",
                }
            elif params["type"] == "kem":
                kem = KeyEncapsulation(algorithm.value)
                public_key = kem.generate_keypair()
                return {
                    "public_key": kem.public_key,
                    "private_key": kem.secret_key,
                    "algorithm": algorithm.value,
                    "type": "kem",
                }
        else:
            # Fallback para algoritmo clássico (simulado)
            logger.info(f"🔄 Usando fallback para {algorithm.value}")
            return self._generate_classic_keypair(algorithm)

    def _generate_classic_keypair(self, algorithm: PQCAlgorithm) -> Dict[str, bytes]:
        """Gera par de chaves clássico (simulado para demonstração)."""
        # Em produção: usar cryptography library para RSA/ECDSA
        import os
        return {
            "public_key": os.urandom(256),  # Simulado
            "private_key": os.urandom(256),  # Simulado
            "algorithm": algorithm.value,
            "type": "signature" if "DILITHIUM" in algorithm.value or "SPHINCS" in algorithm.value else "kem",
            "fallback": True,
        }

    def sign_message(
        self,
        message: Union[str, bytes],
        private_key: bytes,
        algorithm: Optional[PQCAlgorithm] = None,
        hybrid: Optional[bool] = None,
    ) -> CryptoOperationResult:
        """Assina mensagem com algoritmo PQC ou clássico."""
        algorithm = algorithm or self.config.primary_algorithm
        hybrid = hybrid if hybrid is not None else self.config.hybrid_mode

        try:
            # Converter mensagem para bytes se necessário
            if isinstance(message, str):
                message = message.encode('utf-8')

            pqc_signature = None
            classic_signature = None

            # Assinatura PQC principal
            if self._pqc_available and algorithm in self.ALGORITHM_PARAMS:
                params = self.ALGORITHM_PARAMS[algorithm]
                if params["type"] == "signature":
                    signer = Signature(algorithm.value, secret_key=private_key)
                    pqc_signature = signer.sign(message)

            # Assinatura clássica para modo híbrido
            if hybrid:
                classic_signature = self._classic_sign(message, private_key)

            # Combinar assinaturas se modo híbrido
            if hybrid and pqc_signature and classic_signature:
                final_signature = pqc_signature + b"||" + classic_signature
            elif pqc_signature:
                final_signature = pqc_signature
            elif classic_signature:
                final_signature = classic_signature
            else:
                return CryptoOperationResult(
                    success=False,
                    algorithm_used=algorithm.value,
                    error_message="Nenhuma assinatura gerada",
                    pqc_fallback_used=not self._pqc_available,
                )

            return CryptoOperationResult(
                success=True,
                algorithm_used=algorithm.value,
                signature_or_ciphertext=final_signature,
                pqc_fallback_used=not self._pqc_available,
            )

        except Exception as e:
            logger.error(f"❌ Erro ao assinar mensagem: {e}")
            return CryptoOperationResult(
                success=False,
                algorithm_used=algorithm.value,
                error_message=str(e),
                pqc_fallback_used=not self._pqc_available,
            )

    def verify_signature(
        self,
        message: Union[str, bytes],
        signature: bytes,
        public_key: bytes,
        algorithm: Optional[PQCAlgorithm] = None,
        hybrid: Optional[bool] = None,
    ) -> CryptoOperationResult:
        """Verifica assinatura PQC ou clássica."""
        algorithm = algorithm or self.config.primary_algorithm
        hybrid = hybrid if hybrid is not None else self.config.hybrid_mode

        try:
            if isinstance(message, str):
                message = message.encode('utf-8')

            # Separar assinaturas se modo híbrido
            if hybrid and b"||" in signature:
                pqc_sig, classic_sig = signature.split(b"||", 1)
            else:
                pqc_sig = signature if self._pqc_available else None
                classic_sig = signature if not self._pqc_available else None

            pqc_valid = False
            classic_valid = False

            # Verificar assinatura PQC
            if pqc_sig and self._pqc_available and algorithm in self.ALGORITHM_PARAMS:
                params = self.ALGORITHM_PARAMS[algorithm]
                if params["type"] == "signature":
                    verifier = Signature(algorithm.value, public_key=public_key)
                    pqc_valid = verifier.verify(message, pqc_sig)

            # Verificar assinatura clássica
            if classic_sig:
                classic_valid = self._classic_verify(message, classic_sig, public_key)

            # Resultado final baseado em modo híbrido
            if hybrid:
                valid = pqc_valid or classic_valid  # Pelo menos uma válida
            else:
                valid = pqc_valid if pqc_sig is not None else classic_valid

            return CryptoOperationResult(
                success=valid,
                algorithm_used=algorithm.value,
                verification_result=valid,
                pqc_fallback_used=not self._pqc_available,
            )

        except Exception as e:
            logger.error(f"❌ Erro ao verificar assinatura: {e}")
            return CryptoOperationResult(
                success=False,
                algorithm_used=algorithm.value,
                error_message=str(e),
                pqc_fallback_used=not self._pqc_available,
            )

    def _classic_sign(self, message: bytes, private_key: bytes) -> bytes:
        """Assinatura clássica simulada (RSA/ECDSA)."""
        # Em produção: usar cryptography library
        import hashlib
        return hashlib.sha3_256(message + private_key).digest()

    def _classic_verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verificação clássica simulada."""
        import hashlib
        expected = hashlib.sha3_256(message + public_key).digest()
        return signature == expected

    def generate_integrity_proof(
        self,
        operation_result: CryptoOperationResult,
        context: Optional[Dict] = None,
    ) -> str:
        """Gera prova de integridade SHA3-256 para operação criptográfica."""
        proof_data = {
            "algorithm": operation_result.algorithm_used,
            "success": operation_result.success,
            "timestamp": operation_result.timestamp,
            "pqc_fallback": operation_result.pqc_fallback_used,
            "context": context or {},
        }

        if operation_result.signature_or_ciphertext:
            # Hash da assinatura/ciphertext (não o conteúdo completo)
            proof_data["signature_hash"] = hashlib.sha3_256(
                operation_result.signature_or_ciphertext
            ).hexdigest()[:16]

        return hashlib.sha3_256(
            json.dumps(proof_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

    def rotate_keys(
        self,
        old_keypair: Dict[str, bytes],
        algorithm: Optional[PQCAlgorithm] = None,
    ) -> Tuple[Dict[str, bytes], str]:
        """Rotação de chaves com ancoragem temporal."""
        new_keypair = self.generate_keypair(algorithm)

        # Gerar selo de transição
        transition_seal = hashlib.sha3_256(
            json.dumps({
                "old_pubkey_hash": hashlib.sha3_256(old_keypair["public_key"]).hexdigest(),
                "new_pubkey_hash": hashlib.sha3_256(new_keypair["public_key"]).hexdigest(),
                "algorithm": algorithm.value if algorithm else self.config.primary_algorithm.value,
                "timestamp": time.time(),
            }, sort_keys=True).encode()
        ).hexdigest()[:16]

        return new_keypair, transition_seal
