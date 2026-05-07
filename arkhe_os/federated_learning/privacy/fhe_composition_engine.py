"""
Engine de composição FHE para operações criptográficas em gradientes bancários.
Suporta CKKS para operações aproximadas (gradientes floats) e BFV/BGV para exatas.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import hashlib

class FHEScheme(Enum):
    """Esquemas FHE suportados para diferentes tipos de operação."""
    CKKS = "ckks"      # Aproximado: ideal para gradientes floats, operações lineares
    BFV = "bfv"        # Exato: ideal para contagens, operações discretas
    BGV = "bgv"        # Exato: alternativa a BFV com diferentes tradeoffs

@dataclass
class FHEParameters:
    """Parâmetros criptográficos para esquema FHE."""
    scheme: FHEScheme
    poly_modulus_degree: int  # Grau do polinômio módulo (ex: 2^14)
    coeff_modulus_bits: List[int]  # Bits por módulo de coeficiente
    scale: int  # Fator de escala para CKKS (ex: 2^40)
    security_level: int  # Nível de segurança em bits (ex: 128)

    @property
    def max_multiplicative_depth(self) -> int:
        """Profundidade multiplicativa máxima suportada."""
        # Estimativa baseada em parâmetros (simplificada)
        return len(self.coeff_modulus_bits) - 2

@dataclass
class EncryptedGradient:
    """Gradiente encryptado com metadata para verificação."""
    ciphertext: bytes  # Ciphertext FHE serializado
    scheme: FHEScheme
    institution_id: str
    round_id: str
    gradient_hash: str  # Hash do gradiente plaintext para auditoria (não revela valor)
    dp_noise_scale: float  # Escala do ruído DP aplicado
    compliance_proof_hash: Optional[str] = None  # Hash do proof ZK de compliance local

    def verify_integrity(self, expected_hash: str) -> bool:
        """Verifica integridade do ciphertext via hash comprometido."""
        return hashlib.sha256(self.ciphertext).hexdigest()[:16] == expected_hash[:16]

class FHECompositionEngine:
    """Engine para composição de operações FHE em contexto federado bancário."""

    def __init__(self, default_params: FHEParameters):
        self.default_params = default_params
        self.contexts: Dict[str, any] = {}  # Contextos FHE por scheme+params
        self.encryptors: Dict[str, any] = {}
        self.evaluators: Dict[str, any] = {}

    def initialize_context(self, params: FHEParameters) -> str:
        """Inicializa contexto FHE para parâmetros específicos."""
        context_id = f"{params.scheme.value}_{params.poly_modulus_degree}_{hash(tuple(params.coeff_modulus_bits))}"

        if context_id not in self.contexts:
            # Em produção: inicializar contexto real via SEAL/HElib/OpenFHE
            self.contexts[context_id] = {
                "scheme": params.scheme,
                "params": params,
                "initialized": True,
                "max_depth": params.max_multiplicative_depth
            }
            self.encryptors[context_id] = f"encryptor_{context_id}"
            self.evaluators[context_id] = f"evaluator_{context_id}"

        return context_id

    def encrypt_gradient(self, gradient: np.ndarray, params: FHEParameters,
                        institution_id: str, round_id: str,
                        dp_noise_scale: float) -> EncryptedGradient:
        """
        Encrypta gradiente com FHE após aplicação de ruído DP.

        Args:
            gradient: Gradiente local (np.ndarray)
            params: Parâmetros FHE
            institution_id: Identificador da instituição
            round_id: Identificador do round federado
            dp_noise_scale: Escala do ruído Laplace para differential privacy

        Returns:
            EncryptedGradient com ciphertext e metadata
        """
        # 1. Aplicar ruído differential privacy
        noisy_gradient = gradient + np.random.laplace(0, dp_noise_scale, gradient.shape)

        # 2. Calcular hash para auditoria (não revela valor, apenas integridade)
        gradient_hash = hashlib.sha256(
            noisy_gradient.tobytes() + institution_id.encode() + round_id.encode()
        ).hexdigest()[:16]

        # 3. Encryptar via FHE (simulado)
        context_id = self.initialize_context(params)

        # Em produção: ciphertext = encryptor.Encrypt(noisy_gradient, params)
        # Aqui: simular ciphertext como bytes serializados + metadata
        ciphertext = hashlib.sha256(
            noisy_gradient.tobytes() + context_id.encode() + str(dp_noise_scale).encode()
        ).digest()

        return EncryptedGradient(
            ciphertext=ciphertext,
            scheme=params.scheme,
            institution_id=institution_id,
            round_id=round_id,
            gradient_hash=gradient_hash,
            dp_noise_scale=dp_noise_scale
        )

    def homomorphic_aggregate(self, encrypted_gradients: List[EncryptedGradient]) -> EncryptedGradient:
        """
        Agrega gradientes encryptados homomorficamente.

        Requer que todos os gradientes usem o mesmo scheme e parâmetros.
        """
        if not encrypted_gradients:
            raise ValueError("Nenhum gradiente para agregar")

        # Verificar compatibilidade de parâmetros
        first = encrypted_gradients[0]
        for eg in encrypted_gradients[1:]:
            if eg.scheme != first.scheme:
                raise ValueError(f"Mismatch de scheme: {eg.scheme} vs {first.scheme}")
            # Em produção: verificar compatibilidade de parâmetros criptográficos

        # Agregação homomórfica (simulada)
        # Em produção: aggregated = evaluator.AddMany([eg.ciphertext for eg in encrypted_gradients])
        aggregated_ciphertext = hashlib.sha256(
            b"".join(eg.ciphertext for eg in encrypted_gradients) +
            f"aggregate_{len(encrypted_gradients)}".encode()
        ).digest()

        # Metadata agregada
        aggregated_hash = hashlib.sha256(
            b"".join(eg.gradient_hash.encode() for eg in encrypted_gradients)
        ).hexdigest()[:16]

        return EncryptedGradient(
            ciphertext=aggregated_ciphertext,
            scheme=first.scheme,
            institution_id="AGGREGATED",
            round_id=first.round_id,
            gradient_hash=aggregated_hash,
            dp_noise_scale=sum(eg.dp_noise_scale for eg in encrypted_gradients) / len(encrypted_gradients)
        )

    def generate_compliance_proof(self, encrypted_gradient: EncryptedGradient,
                                 compliance_predicates: List[str]) -> str:
        """
        Gera proof ZK via Zinc+ de que o gradiente encryptado satisfaz predicados de compliance.

        Retorna hash do proof para verificação posterior.
        """
        # Em produção: compilar predicados para circuito Zinc+, gerar proof
        # Aqui: simular proof hash baseado em inputs
        proof_input = (
            encrypted_gradient.ciphertext +
            encrypted_gradient.gradient_hash.encode() +
            b"".join(p.encode() for p in compliance_predicates) +
            encrypted_gradient.institution_id.encode()
        )
        proof_hash = hashlib.sha256(proof_input).hexdigest()

        return proof_hash
