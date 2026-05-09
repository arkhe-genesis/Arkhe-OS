# arkhe_os/orchestrator/privacy/fhe_compositional.py
"""
FHE composicional para proteção de embeddings latentes e estados recorrentes
durante agregação federada de modelos de difusão.
"""
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

class FHEScheme(Enum):
    """Esquemas FHE suportados para composição."""
    CKKS = "ckks"    # Aproximado: ideal para floats em embeddings
    BFV = "bfv"      # Exato: ideal para ints em índices/estados discretos
    BGV = "bgv"      # Exato: alternativa a BFV com diferentes tradeoffs

@dataclass
class FHELayerConfig:
    """Configuração de uma camada na composição FHE."""
    scheme: FHEScheme
    poly_modulus_degree: int      # Grau do polinômio módulo
    coeff_modulus_bits: List[int] # Bits por módulo de coeficiente
    scale: int                    # Fator de escala (CKKS apenas)
    max_depth: int                # Profundidade multiplicativa suportada

    @property
    def security_level(self) -> int:
        """Estimativa de nível de segurança em bits."""
        # Estimativa simplificada baseada em parâmetros
        return min(128, self.poly_modulus_degree // 16)

@dataclass
class EncryptedTensor:
    """Tensor encryptado com metadata para agregação federada."""
    ciphertexts: List[bytes]      # Lista de ciphertexts por componente
    scheme: FHEScheme
    shape: Tuple[int, ...]        # Forma original do tensor
    layer_configs: List[FHELayerConfig]  # Configurações por camada de composição
    federation_id: str            # ID da federação para rastreamento
    dp_noise_scale: float         # Escala de ruído DP aplicado
    metadata: Dict = field(default_factory=dict)

    def verify_integrity(self, expected_hash: str) -> bool:
        """Verifica integridade via hash comprometido."""
        import hashlib
        combined = b"".join(self.ciphertexts) + self.federation_id.encode()
        actual_hash = hashlib.sha256(combined).hexdigest()[:16]
        return actual_hash == expected_hash[:16]

class CompositionalFHEEngine:
    """
    Engine para composição de múltiplos esquemas FHE em tensores de difusão.

    Suporta: CKKS para embeddings floats, BFV/BGV para estados discretos,
    com composição segura para operações profundas.
    """

    def __init__(self, default_config: FHELayerConfig):
        self.default_config = default_config
        self.contexts: Dict[str, any] = {}  # Contextos FHE por scheme+params
        self._initialize_contexts()

    def _initialize_contexts(self):
        """Inicializa contextos FHE para esquemas suportados."""
        # Em produção: inicializar contextos reais via OpenFHE/SEAL
        for scheme in FHEScheme:
            key = f"{scheme.value}_{self.default_config.poly_modulus_degree}"
            self.contexts[key] = {
                'scheme': scheme,
                'config': self.default_config,
                'initialized': True
            }

    def encrypt_diffusion_tensor(
        self,
        tensor: np.ndarray,
        tensor_type: str,  # 'embedding', 'recurrent_state', 'gradient'
        federation_id: str,
        dp_config: Optional[Dict] = None
    ) -> EncryptedTensor:
        """
        Encrypta tensor de difusão com FHE composicional + DP.

        Args:
            tensor: Tensor numpy a ser encryptado
            tensor_type: Tipo do tensor para selecionar esquema apropriado
            federation_id: ID da federação para rastreamento
            dp_config: Configuração opcional de differential privacy

        Returns:
            EncryptedTensor com ciphertexts e metadata
        """
        # Aplicar differential privacy se configurado
        if dp_config:
            noise_scale = dp_config.get('noise_scale', 0.0)
            if noise_scale > 0:
                if dp_config.get('mechanism', 'laplace') == 'laplace':
                    tensor = tensor + np.random.laplace(0, noise_scale, tensor.shape)
                elif dp_config.get('mechanism') == 'gaussian':
                    tensor = tensor + np.random.normal(0, noise_scale, tensor.shape)
                tensor = np.clip(tensor, -10.0, 10.0)  # Limitar para estabilidade numérica

        # Selecionar esquema baseado no tipo de tensor
        if tensor_type == 'embedding':
            # Embeddings: floats → CKKS para operações aproximadas
            scheme = FHEScheme.CKKS
            scale = self.default_config.scale
        elif tensor_type in ['recurrent_state', 'gradient']:
            # Estados/gradientes: podem ser discretos → BFV para exatidão
            scheme = FHEScheme.BFV
            scale = None
        else:
            scheme = self.default_config.scheme
            scale = self.default_config.scale

        # Encryptar tensor (simulado - em produção: chamada real ao FHE)
        context_key = f"{scheme.value}_{self.default_config.poly_modulus_degree}"

        # Dividir tensor em chunks para parallel encryption
        chunk_size = min(1024, np.prod(tensor.shape) // 4)
        if chunk_size == 0:
            chunk_size = 1
        chunks = [tensor.flat[i:i+chunk_size] for i in range(0, len(tensor.flat), chunk_size)]

        ciphertexts = []
        for chunk in chunks:
            # Em produção: ciphertext = encryptor.Encrypt(chunk, context)
            # Aqui: simular ciphertext como hash + metadata
            import hashlib
            chunk_hash = hashlib.sha256(
                chunk.tobytes() + context_key.encode() +
                (str(scale).encode() if scale else b'')
            ).digest()
            ciphertexts.append(chunk_hash)

        return EncryptedTensor(
            ciphertexts=ciphertexts,
            scheme=scheme,
            shape=tensor.shape,
            layer_configs=[self.default_config],
            federation_id=federation_id,
            dp_noise_scale=dp_config.get('noise_scale', 0.0) if dp_config else 0.0,
            metadata={'tensor_type': tensor_type, 'original_dtype': str(tensor.dtype)}
        )

    def homomorphic_aggregate(
        self,
        encrypted_tensors: List[EncryptedTensor],
        weights: Optional[List[float]] = None
    ) -> EncryptedTensor:
        """
        Agrega tensores encryptados homomorficamente com pesos opcionais.

        Requer que todos os tensores usem o mesmo scheme e parâmetros.
        """
        if not encrypted_tensors:
            raise ValueError("Nenhum tensor para agregar")

        # Verificar compatibilidade
        first = encrypted_tensors[0]
        for et in encrypted_tensors[1:]:
            if et.scheme != first.scheme:
                raise ValueError(f"Mismatch de scheme: {et.scheme} vs {first.scheme}")
            if et.layer_configs != first.layer_configs:
                raise ValueError("Configurações de camada incompatíveis")

        # Aplicar pesos se fornecidos
        if weights:
            if len(weights) != len(encrypted_tensors):
                raise ValueError("Número de pesos não corresponde ao número de tensores")
            # Em produção: multiplicar ciphertexts por pesos homomorficamente
            # Aqui: simular ponderação via metadata
            weighted_tensors = []
            for et, w in zip(encrypted_tensors, weights):
                # Simular: ciphertexts ponderados
                weighted_ciphertexts = [
                    bytes([int(b * w) % 256 for b in ct]) if w != 1.0 else ct
                    for ct in et.ciphertexts
                ]
                weighted_tensors.append(EncryptedTensor(
                    ciphertexts=weighted_ciphertexts,
                    scheme=et.scheme,
                    shape=et.shape,
                    layer_configs=et.layer_configs,
                    federation_id=et.federation_id,
                    dp_noise_scale=et.dp_noise_scale * w,
                    metadata={**et.metadata, 'weight': w}
                ))
            encrypted_tensors = weighted_tensors

        # Agregação homomórfica (simulada)
        import hashlib
        aggregated_ciphertexts = []
        for i in range(len(first.ciphertexts)):
            combined = b"".join(et.ciphertexts[i] for et in encrypted_tensors)
            agg_hash = hashlib.sha256(
                combined + f"aggregate_{len(encrypted_tensors)}".encode()
            ).digest()
            aggregated_ciphertexts.append(agg_hash)

        # Metadata agregada
        avg_dp_noise = np.mean([et.dp_noise_scale for et in encrypted_tensors])

        return EncryptedTensor(
            ciphertexts=aggregated_ciphertexts,
            scheme=first.scheme,
            shape=first.shape,
            layer_configs=first.layer_configs,
            federation_id=f"AGGREGATED_{first.federation_id}",
            dp_noise_scale=avg_dp_noise,
            metadata={
                'aggregation_type': 'weighted_sum' if weights else 'uniform_sum',
                'contributor_count': len(encrypted_tensors),
                'contributor_federations': list(set(et.federation_id for et in encrypted_tensors))
            }
        )

    def generate_privacy_proof(
        self,
        aggregated: EncryptedTensor,
        dp_epsilon: float,
        dp_delta: float
    ) -> Dict:
        """
        Gera proof ZK de que a agregação preserva differential privacy.

        Returns:
            Dict com proof serializado para verificação pública
        """
        import hashlib
        import json

        # Construir statement para o proof:
        # "A agregação de tensores encryptados com ruído DP(ε,δ) preserva (ε,δ)-DP"
        proof_statement = {
            'aggregation_hash': hashlib.sha256(
                b"".join(aggregated.ciphertexts)
            ).hexdigest(),
            'dp_parameters': {'epsilon': dp_epsilon, 'delta': dp_delta},
            'contributor_count': aggregated.metadata.get('contributor_count', 0),
            'scheme': aggregated.scheme.value,
            'federation_id': aggregated.federation_id
        }

        # Em produção: gerar proof ZK real via Zinc+
        # Aqui: simular proof hash baseado no statement
        proof_hash = hashlib.sha256(
            json.dumps(proof_statement, sort_keys=True).encode()
        ).hexdigest()

        return {
            'proof_id': f"priv_proof_{proof_hash[:16]}",
            'statement_hash': hashlib.sha256(
                json.dumps(proof_statement, sort_keys=True).encode()
            ).hexdigest()[:32],
            'proof_blob': proof_hash,  # Simulado
            'verification_key_hash': hashlib.sha256(
                f"dp_privacy_proof_v1_{aggregated.scheme.value}".encode()
            ).hexdigest()[:16],
            'metadata': {
                'dp_epsilon': dp_epsilon,
                'dp_delta': dp_delta,
                'aggregation_scheme': aggregated.scheme.value,
                'generated_at': np.datetime64('now').item().isoformat()
            }
        }
