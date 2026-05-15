#!/usr/bin/env python3
"""
Substrato 187: Assinatura Visual para Cápsulas PQC
Gera QR-code ASCII a partir de hash PQC e anexa como metadata visual
para verificação rápida de integridade sem depender de ferramentas criptográficas.
"""

import hashlib
import json
import time
from typing import Dict, Optional
from dataclasses import dataclass
import logging

from risomorphism.engine.real_image_processor import RealImageProcessor, ImageProcessingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VisualSignatureConfig:
    """Configuração para assinatura visual PQC."""
    preset: str = "stroke-clarity"
    scale: int = 2  # Pequeno para QR-code
    include_hash_prefix: bool = True
    hash_prefix_length: int = 16
    border_chars: str = "╔═╗║║╚═╝"  # Bordas decorativas

class VisualPQCSignature:
    """
    Gera assinatura visual ASCII para cápsulas PQC.

    Características:
    • QR-code ASCII gerado a partir de hash PQC (determinístico)
    • Metadata legível anexada (algoritmo, timestamp, key_id)
    • Bordas decorativas para delimitação visual
    • Hash de integridade SHA3-256 da assinatura visual
    • Ancoragem na TemporalChain para auditoria
    """

    # Mapa simples para "QR-code" ASCII (simulado para demo)
    # Em produção: usar biblioteca real de QR-code → ASCII
    QR_PATTERN = [
        "██████████████",
        "██  ██  ██  ██",
        "██  ██  ██  ██",
        "██  ██████  ██",
        "██  ██  ██  ██",
        "██    ██    ██",
        "██████████████",
    ]

    def __init__(self, config: Optional[VisualSignatureConfig] = None):
        self.config = config or VisualSignatureConfig()
        self.processor = RealImageProcessor(ImageProcessingConfig())

    async def generate_visual_signature(
        self,
        pqc_signature_hex: str,
        capsule_metadata: Dict,
        temporal_chain=None,
    ) -> Dict:
        """
        Gera assinatura visual ASCII para cápsula PQC.

        Args:
            pqc_signature_hex: Assinatura PQC em hexadecimal
            capsule_metadata: Metadados da cápsula para inclusão visual
            temporal_chain: Instância opcional para ancoragem

        Returns:
            Dict com assinatura visual, hash de integridade e selo temporal
        """
        # 1. Calcular hash de referência para o "QR-code"
        qr_seed = hashlib.sha3_256(pqc_signature_hex.encode()).hexdigest()[:8]

        # 2. Gerar padrão ASCII simulando QR-code (determinístico pelo seed)
        qr_ascii = self._generate_ascii_qr(qr_seed)

        # 3. Construir metadata legível
        metadata_lines = [
            f"PQC:{capsule_metadata.get('algorithm', 'Dilithium-3')}",
            f"KEY:{capsule_metadata.get('key_id', 'unknown')[:8]}",
            f"TS:{int(capsule_metadata.get('timestamp', time.time()))}",
        ]

        # 4. Adicionar prefixo do hash se configurado
        if self.config.include_hash_prefix:
            hash_prefix = pqc_signature_hex[:self.config.hash_prefix_length]
            metadata_lines.insert(0, f"#{hash_prefix}")

        # 5. Montar assinatura visual com bordas
        border = self.config.border_chars
        width = max(len(qr_ascii.split('\n')[0]), max(len(m) for m in metadata_lines))

        visual_signature = f"{border[0]}{'═' * width}{border[2]}\n"
        visual_signature += f"{border[3]}{qr_ascii.ljust(width)}{border[3]}\n"
        for meta in metadata_lines:
            visual_signature += f"{border[3]}{meta.ljust(width)}{border[3]}\n"
        visual_signature += f"{border[4]}{'═' * width}{border[5]}\n"

        # 6. Calcular hash de integridade da assinatura visual
        integrity_hash = hashlib.sha3_256(visual_signature.encode()).hexdigest()

        # 7. Ancorar na TemporalChain se disponível
        temporal_seal = None
        if temporal_chain:
            temporal_seal = await temporal_chain.anchor_event(
                "visual_pqc_signature_generated",
                {
                    "pqc_hash_prefix": pqc_signature_hex[:16],
                    "visual_hash": integrity_hash[:16],
                    "algorithm": capsule_metadata.get("algorithm"),
                    "key_id": capsule_metadata.get("key_id"),
                    "timestamp": time.time(),
                }
            )

        return {
            "visual_signature": visual_signature,
            "integrity_hash": integrity_hash,
            "temporal_seal": temporal_seal,
            "qr_seed": qr_seed,
            "metadata_lines": metadata_lines,
            "generated_at": time.time(),
        }

    def _generate_ascii_qr(self, seed: str) -> str:
        """Gera padrão ASCII simulando QR-code baseado em seed determinístico."""
        # Simulação: usar seed para variar padrão básico
        pattern = []
        for i, row in enumerate(self.QR_PATTERN):
            # Variar caracteres baseado no seed + índice
            varied_row = ""
            for j, char in enumerate(row):
                if char == "█":
                    # Escolher caractere baseado em hash da posição + seed
                    selector = hashlib.sha3_256(f"{seed}:{i}:{j}".encode()).hexdigest()[:2]
                    varied_row += "█" if int(selector, 16) % 2 == 0 else "▓"
                else:
                    varied_row += char
            pattern.append(varied_row)
        return "\n".join(pattern)

    def verify_visual_signature(self, visual_signature: str, expected_hash: str) -> bool:
        """Verifica integridade de assinatura visual via hash SHA3-256."""
        computed_hash = hashlib.sha3_256(visual_signature.encode()).hexdigest()
        return computed_hash == expected_hash
