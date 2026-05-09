# arkhe_os/mrc/dynamic_srv6_controller.py
"""
API de controle para configuração dinâmica de rotas SRv6 com validação
de coerência por segmento e otimização baseada em métricas em tempo real.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Callable
from collections import defaultdict
from enum import Enum
import hashlib
import time

class SRv6SegmentType(Enum):
    NODE = "node"          # uN: Micro-Node SID (próximo router)
    ADJACENCY = "adjacency" # uA: Micro-Adjacency SID (link específico)
    ENDPOINT = "endpoint"   # Destino final

@dataclass
class SRv6Segment:
    """Representação de segmento SRv6."""
    segment_id: str
    segment_type: SRv6SegmentType
    sid_value: str              # Micro-SID value (hex)
    node_id: str                # Identificador do nó/router
    link_id: Optional[str] = None  # Para tipo adjacency
    coherence_weight: float = 1.0  # Peso de coerência para este segmento
    metadata: Dict = field(default_factory=dict)

    def __hash__(self):
        return hash(self.segment_id)

@dataclass
class SRv6Route:
    """Rota SRv6 completa com validação de coerência."""
    route_id: str
    source_node: str
    dest_node: str
    segments: List[SRv6Segment]
    expected_coherence: float   # Φ_C esperado para rota completa
    actual_coherence: Optional[float] = None  # Φ_C medido (se disponível)
    created_at: float = field(default_factory=time.time)
    last_validated: float = 0.0
    validation_status: str = "pending"  # pending/valid/invalid
    metadata: Dict = field(default_factory=dict)

    def compute_route_coherence(self, segment_coherences: Dict[str, float]) -> float:
        """
        Calcula coerência da rota baseada em coerências dos segmentos.

        Fórmula: Φ_route = Π Φ_segment * exp(-μ * divergência entre segmentos)
        """
        if not self.segments:
            return 0.0

        # Produto das coerências dos segmentos
        product_coherence = 1.0
        for seg in self.segments:
            seg_coh = segment_coherences.get(seg.segment_id, 0.5)  # Default 0.5 se desconhecido
            product_coherence *= seg_coh * seg.coherence_weight

        # Penalidade por divergência entre segmentos consecutivos
        divergence_penalty = 0.0
        mu = 0.1  # Fator de penalização
        for i in range(len(self.segments) - 1):
            seg1 = self.segments[i]
            seg2 = self.segments[i + 1]
            # Divergência simples: diferença de node_id ou link_id
            if seg1.node_id != seg2.node_id and seg1.link_id != seg2.link_id:
                divergence_penalty += mu

        return product_coherence * np.exp(-divergence_penalty)

    def validate_coherence(
        self,
        segment_coherences: Dict[str, float],
        min_coherence: float = 0.7,
    ) -> Tuple[bool, str]:
        """
        Valida se rota atende threshold de coerência.

        Returns:
            (is_valid, reason)
        """
        computed = self.compute_route_coherence(segment_coherences)
        self.actual_coherence = computed
        self.last_validated = time.time()

        if computed >= min_coherence:
            self.validation_status = "valid"
            return True, f"Coherence {computed:.3f} >= threshold {min_coherence}"
        else:
            self.validation_status = "invalid"
            return False, f"Coherence {computed:.3f} < threshold {min_coherence}"

class DynamicSRv6Controller:
    """
    Controlador para configuração dinâmica de rotas SRv6.

    Funcionalidades:
    - Criação/validação de rotas com coerência
    - Atualização dinâmica baseada em métricas em tempo real
    - Fallback automático para rotas alternativas
    - API para integração com control-plane externo
    """

    def __init__(
        self,
        node_id: str,
        coherence_threshold: float = 0.7,
        max_route_segments: int = 8,
        validation_interval: float = 5.0,  # Validar rotas a cada 5s
    ):
        self.node_id = node_id
        self.min_coherence = coherence_threshold
        self.max_segments = max_route_segments
        self.validation_interval = validation_interval

        # Estado interno
        self.segments_registry: Dict[str, SRv6Segment] = {}
        self.active_routes: Dict[str, SRv6Route] = {}
        self.segment_coherences: Dict[str, float] = {}  # Coerência atual por segmento
        self.route_usage: Dict[str, int] = defaultdict(int)  # Contagem de uso por rota

        # Cache de validação
        self.last_validation: Dict[str, float] = {}

        # Callbacks
        self.on_route_invalidated: Optional[Callable] = None
        self.on_coherence_updated: Optional[Callable] = None

        # Estatísticas
        self.stats = {
            'routes_created': 0,
            'routes_validated': 0,
            'routes_invalidated': 0,
            'avg_route_coherence': 0.0,
        }

    def register_segment(
        self,
        segment_id: str,
        segment_type: SRv6SegmentType,
        sid_value: str,
        node_id: str,
        link_id: Optional[str] = None,
        initial_coherence: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Registra novo segmento SRv6 no registry."""
        if segment_id in self.segments_registry:
            return False  # Já existe

        segment = SRv6Segment(
            segment_id=segment_id,
            segment_type=segment_type,
            sid_value=sid_value,
            node_id=node_id,
            link_id=link_id,
            coherence_weight=1.0,
            metadata=metadata or {},
        )

        self.segments_registry[segment_id] = segment
        self.segment_coherences[segment_id] = initial_coherence

        return True

    def create_route(
        self,
        route_id: str,
        source_node: str,
        dest_node: str,
        segment_ids: List[str],
        expected_coherence: float,
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """
        Cria nova rota SRv6 com validação inicial de coerência.

        Returns:
            (success, message)
        """
        # Validar segmento IDs
        for seg_id in segment_ids:
            if seg_id not in self.segments_registry:
                return False, f"Segment {seg_id} not registered"

        if len(segment_ids) > self.max_segments:
            return False, f"Route exceeds max segments ({self.max_segments})"

        # Construir rota
        segments = [self.segments_registry[sid] for sid in segment_ids]
        route = SRv6Route(
            route_id=route_id,
            source_node=source_node,
            dest_node=dest_node,
            segments=segments,
            expected_coherence=expected_coherence,
            metadata=metadata or {},
        )

        # Validar coerência inicial
        is_valid, reason = route.validate_coherence(
            self.segment_coherences,
            self.min_coherence,
        )

        if not is_valid:
            return False, f"Route validation failed: {reason}"

        # Registrar rota ativa
        self.active_routes[route_id] = route
        self.stats['routes_created'] += 1

        return True, f"Route {route_id} created and validated"

    def update_segment_coherence(
        self,
        segment_id: str,
        new_coherence: float,
        source: str = "measurement",  # measurement/probe/estimate
    ) -> bool:
        """
        Atualiza coerência de segmento e revalida rotas afetadas.

        Returns:
            True se atualizações foram aplicadas
        """
        if segment_id not in self.segment_coherences:
            return False

        old_coherence = self.segment_coherences[segment_id]
        self.segment_coherences[segment_id] = new_coherence

        # Notificar callback se houver mudança significativa
        if self.on_coherence_updated and abs(new_coherence - old_coherence) > 0.1:
            self.on_coherence_updated(segment_id, old_coherence, new_coherence, source)

        # Revalidar rotas que usam este segmento
        affected_routes = [
            route for route in self.active_routes.values()
            if any(seg.segment_id == segment_id for seg in route.segments)
        ]

        for route in affected_routes:
            self._revalidate_route(route)

        return True

    def get_optimal_route(
        self,
        source_node: str,
        dest_node: str,
        min_coherence: Optional[float] = None,
        max_segments: Optional[int] = None,
    ) -> Optional[SRv6Route]:
        """
        Encontra rota ótima entre origem e destino baseada em coerência.

        Returns:
            SRv6Route com maior coerência válida, ou None se não encontrar
        """
        threshold = min_coherence or self.min_coherence
        max_segs = max_segments or self.max_segments

        candidates = []
        for route in self.active_routes.values():
            if (route.source_node == source_node and
                route.dest_node == dest_node and
                len(route.segments) <= max_segs):

                # Validar se ainda está válida
                if route.validation_status != "valid":
                    is_valid, _ = route.validate_coherence(
                        self.segment_coherences, threshold
                    )
                    if not is_valid:
                        continue

                candidates.append(route)

        if not candidates:
            return None

        # Retornar rota com maior coerência
        return max(candidates, key=lambda r: r.actual_coherence or r.expected_coherence)

    def _revalidate_route(self, route: SRv6Route) -> bool:
        """Revalida coerência de rota e notifica se invalidada."""
        now = time.time()
        last_val = self.last_validation.get(route.route_id, 0)

        # Respeitar intervalo de validação
        if now - last_val < self.validation_interval:
            return route.validation_status == "valid"

        is_valid, reason = route.validate_coherence(
            self.segment_coherences, self.min_coherence
        )
        self.last_validation[route.route_id] = now
        self.stats['routes_validated'] += 1

        if not is_valid:
            self.stats['routes_invalidated'] += 1
            # Notificar callback se rota foi invalidada
            if self.on_route_invalidated and route.validation_status == "valid":
                self.on_route_invalidated(route.route_id, reason)
            return False

        return True

    def get_route_statistics(self) -> Dict:
        """Retorna estatísticas de rotas para monitoramento."""
        valid_routes = [r for r in self.active_routes.values() if r.validation_status == "valid"]
        avg_coh = (
            np.mean([r.actual_coherence or r.expected_coherence for r in valid_routes])
            if valid_routes else 0.0
        )

        return {
            **self.stats,
            'active_routes': len(self.active_routes),
            'valid_routes': len(valid_routes),
            'avg_route_coherence': round(avg_coh, 4),
            'registered_segments': len(self.segments_registry),
        }

    def export_route_config(self, route_id: str) -> Optional[Dict]:
        """
        Exporta configuração de rota para aplicação no data plane.

        Formato compatível com SRv6 uSID encoding.
        """
        route = self.active_routes.get(route_id)
        if not route or route.validation_status != "valid":
            return None

        # Construir SRv6 address com uSIDs
        lid = "2001:db8::"  # Locator ID (configurável)
        usids = [seg.sid_value for seg in route.segments]

        # SRv6 address: LID + uSID stack (padded to 128 bits)
        sr_address = self._build_srv6_address(lid, usids)

        return {
            'route_id': route_id,
            'sr_address': sr_address,
            'segments': [
                {
                    'id': seg.segment_id,
                    'type': seg.segment_type.value,
                    'sid': seg.sid_value,
                    'node': seg.node_id,
                }
                for seg in route.segments
            ],
            'coherence': route.actual_coherence or route.expected_coherence,
            'metadata': route.metadata,
        }

    def _build_srv6_address(self, lid: str, usids: List[str]) -> str:
        """Constrói endereço SRv6 com LID e stack de uSIDs."""
        # Simplificação: em produção, seguir RFC 8986 para encoding
        # Aqui: concatenar como string para demonstração
        usid_str = ":".join(usids[:6])  # Máx 6 uSIDs em 128 bits
        return f"{lid.rstrip(':')}:{usid_str}" if usids else lid
