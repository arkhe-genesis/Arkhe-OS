# arkhe_os/mrc/syndrome_decoder_bridge.py
"""
Bridge entre MRC Packet Trimming e Substrato 120 (Surface Code Error Correction)
Mapeia pacotes trimmados para síndromes parciais e habilita correção antecipada.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import hashlib

class SyndromeType(Enum):
    PARTIAL = "partial"      # Payload trimmado, header intacto
    HEADER_CORRUPT = "header_corrupt"  # Header também comprometido
    FULL_LOSS = "full_loss"  # Pacote perdido completamente

@dataclass
class PartialSyndrome:
    """Representação de síndrome parcial para correção antecipada."""
    packet_id: str
    plane_id: int
    sequence_num: int
    syndrome_type: SyndromeType
    header_hash: str          # Hash do cabeçalho recebido
    expected_syndrome: str    # Síndrome esperada do código de superfície
    partial_syndrome: str     # s_p = header_hash ⊕ expected_syndrome
    coherence_path: float     # Φ_C do caminho onde ocorreu o trimming
    timestamp: float
    metadata: Dict = field(default_factory=dict)

    def is_correctable(self, code_distance: int, min_coherence: float) -> bool:
        """Verifica se síndrome parcial permite correção antecipada."""
        if self.coherence_path < min_coherence:
            return False
        # Peso da síndrome (número de bits diferentes) deve ser ≤ t_code
        syndrome_weight = bin(int(self.partial_syndrome, 16)).count('1')
        return syndrome_weight <= code_distance // 2

class SyndromeDecoderBridge:
    """
    Ponte entre camada MRC e Substrato 120 para decodificação de síndromes parciais.

    Integrações:
    - Substrato 120: Surface Code parameters (distance, threshold)
    - Substrato 125: CTC-Photon interface para medição de coerência de caminho
    - Substrato 256: MRC transport layer para trimming detection
    """

    def __init__(
        self,
        surface_code_distance: int = 7,      # Distance do código de superfície
        min_path_coherence: float = 0.7,     # Φ_C mínimo para tentar correção
        syndrome_cache_size: int = 1024,     # Cache de síndromes recentes
    ):
        self.code_distance = surface_code_distance
        self.min_coherence = min_path_coherence
        self.syndrome_cache: Dict[str, PartialSyndrome] = {}
        self.cache_size = syndrome_cache_size
        self.correction_stats = {
            'attempted': 0,
            'successful': 0,
            'failed_coherence': 0,
            'failed_weight': 0,
        }

    def process_trimmed_packet(
        self,
        packet_header: Dict,
        path_coherence: float,
        surface_code_params: Dict,
    ) -> Optional[PartialSyndrome]:
        """
        Processa pacote trimmado e gera síndrome parcial para correção.

        Args:
            packet_header: Cabeçalho do pacote trimmado (sem payload)
            path_coherence: Φ_C medido para o caminho de transmissão
            surface_code_params: Parâmetros do código de superfície do Substrato 120

        Returns:
            PartialSyndrome se correção for possível, None caso contrário
        """
        # Calcular hash do cabeçalho recebido
        header_bytes = self._serialize_header(packet_header)
        header_hash = hashlib.sha256(header_bytes).hexdigest()

        # Calcular síndrome esperada baseada em metadados do código
        expected_syndrome = self._compute_expected_syndrome(
            packet_header, surface_code_params
        )

        # Calcular síndrome parcial: XOR entre hash recebido e esperado
        partial_syndrome = self._xor_hex_strings(header_hash, expected_syndrome)

        # Criar objeto de síndrome parcial
        syndrome = PartialSyndrome(
            packet_id=packet_header['packet_id'],
            plane_id=packet_header['plane_id'],
            sequence_num=packet_header['sequence_num'],
            syndrome_type=SyndromeType.PARTIAL,
            header_hash=header_hash,
            expected_syndrome=expected_syndrome,
            partial_syndrome=partial_syndrome,
            coherence_path=path_coherence,
            timestamp=packet_header.get('timestamp', 0),
            metadata={
                'source_node': packet_header.get('src'),
                'dest_node': packet_header.get('dest'),
                'tensor_shape': packet_header.get('tensor_shape'),
            }
        )

        # Verificar se é corretável
        if not syndrome.is_correctable(self.code_distance, self.min_coherence):
            if path_coherence < self.min_coherence:
                self.correction_stats['failed_coherence'] += 1
            else:
                self.correction_stats['failed_weight'] += 1
            return None

        # Adicionar ao cache e retornar
        self._add_to_cache(syndrome)
        self.correction_stats['attempted'] += 1
        return syndrome

    def attempt_early_correction(
        self,
        syndrome: PartialSyndrome,
        decoder_backend: 'SurfaceCodeDecoder',  # Do Substrato 120 # type: ignore
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Tenta correção antecipada usando síndrome parcial.

        Args:
            syndrome: Síndrome parcial gerada
            decoder_backend: Instância do decoder do Substrato 120

        Returns:
            (success, recovered_metadata) onde recovered_metadata contém
            informações recuperadas do payload trimmado
        """
        if not syndrome.is_correctable(self.code_distance, self.min_coherence):
            return False, None

        # Chamar decoder do Substrato 120 com síndrome parcial
        success, metadata = decoder_backend.decode_partial_syndrome(
            partial_syndrome=syndrome.partial_syndrome,
            expected_syndrome=syndrome.expected_syndrome,
            code_distance=self.code_distance,
            metadata_context=syndrome.metadata,
        )

        if success:
            self.correction_stats['successful'] += 1
            # Atualizar métricas de coerência com feedback da correção
            self._update_coherence_feedback(syndrome, metadata)
            return True, metadata

        return False, None

    def _serialize_header(self, header: Dict) -> bytes:
        """Serializa cabeçalho para hashing de forma determinística."""
        # Ordenar chaves para consistência
        # Filter unhashable values like lists/dicts to make string sorting reliable, although just str() works for basic types
        sorted_items = sorted((str(k), str(v)) for k, v in header.items())
        return str(sorted_items).encode('utf-8')

    def _compute_expected_syndrome(
        self,
        header: Dict,
        code_params: Dict,
    ) -> str:
        """
        Calcula síndrome esperada baseada em metadados do código de superfície.

        Implementação simplificada: em produção, usaria o encoder do Substrato 120.
        """
        # Metadados relevantes para síndrome: sequence_num, plane_id, tensor metadata
        meta_str = f"{header['sequence_num']}:{header['plane_id']}:{header.get('tensor_shape', '')}"
        # Hash como proxy para síndrome (em produção: encoder real do código)
        return hashlib.sha256(meta_str.encode()).hexdigest()[:16]  # 64 bits

    def _xor_hex_strings(self, hex1: str, hex2: str) -> str:
        """XOR entre duas strings hexadecimais."""
        # Converter para int, XOR, voltar para hex
        int1 = int(hex1, 16)
        int2 = int(hex2, 16)
        # 128 bits pad with zeros. However hash length might vary. Let's pad dynamically.
        length = max(len(hex1), len(hex2))
        return format(int1 ^ int2, f'0{length}x')

    def _add_to_cache(self, syndrome: PartialSyndrome):
        """Adiciona síndrome ao cache com LRU eviction."""
        if len(self.syndrome_cache) >= self.cache_size:
            # Remover mais antigo (por timestamp)
            oldest = min(self.syndrome_cache.items(), key=lambda x: x[1].timestamp)
            del self.syndrome_cache[oldest[0]]
        self.syndrome_cache[syndrome.packet_id] = syndrome

    def _update_coherence_feedback(
        self,
        syndrome: PartialSyndrome,
        recovered_metadata: Dict,
    ):
        """
        Atualiza métricas de coerência com feedback da correção bem-sucedida.

        Integra com Substrato 256 para ajustar futuros decisions de trimming.
        """
        # Em produção: enviar para CoherenceGradientChannel do Substrato 256
        feedback = {
            'packet_id': syndrome.packet_id,
            'path_coherence_before': syndrome.coherence_path,
            'correction_success': True,
            'recovered_fields': list(recovered_metadata.keys()),
            'timestamp': syndrome.timestamp,
        }
        # self.coherence_channel.submit_feedback(feedback)  # Interface com Substrato 256
        pass  # Placeholder

    def get_correction_stats(self) -> Dict:
        """Retorna estatísticas de correção para monitoramento."""
        success_rate = (
            self.correction_stats['successful'] /
            max(1, self.correction_stats['attempted'])
        )
        return {
            **self.correction_stats,
            'success_rate': round(success_rate, 4),
            'cache_size': len(self.syndrome_cache),
        }
