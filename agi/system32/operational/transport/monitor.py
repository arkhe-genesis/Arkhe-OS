#!/usr/bin/env python3
"""
transport/monitor.py — Monitor de Coerência para Transportes
Acompanha histórico de Φ_C por transporte e detecta anomalias.
"""
import time
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class TransportCoherenceRecord:
    """Registro de coerência para uma transmissão."""
    timestamp: float
    transport_type: str
    coherence_score: float
    payload_size: int
    destination: str
    success: bool

class CoherenceTransportMonitor:
    """Monitora coerência de transmissões por transporte."""

    def __init__(self, window_size: int = 1000, drift_threshold: float = 0.15):
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.records: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.baselines: Dict[str, float] = {}  # Φ_C baseline por transporte

    def record_transmission(self, transport_type: str, coherence: float,
                           payload_size: int, destination: str, success: bool):
        """Registra uma transmissão para monitoramento."""
        record = TransportCoherenceRecord(
            timestamp=time.time(),
            transport_type=transport_type,
            coherence_score=coherence,
            payload_size=payload_size,
            destination=destination,
            success=success
        )
        self.records[transport_type].append(record)

        # Atualizar baseline se ainda não definido
        if transport_type not in self.baselines and len(self.records[transport_type]) >= 10:
            recent = [r.coherence_score for r in self.records[transport_type][-10:]]
            self.baselines[transport_type] = statistics.mean(recent)
            logger.info(f"📊 Baseline definido para {transport_type}: {self.baselines[transport_type]:.3f}")

    def evaluate_transmission_coherence(self, payload: bytes) -> float:
        """
        Avalia coerência de uma transmissão (placeholder).
        Em produção: usar hash criptográfico + verificação de integridade.
        """
        import hashlib
        # Simplificado: usar entropia do payload como proxy de coerência
        payload_hash = hashlib.sha256(payload).hexdigest()
        # Mapear hash para [0, 1] de forma determinística
        coherence = int(payload_hash[:8], 16) / 0xFFFFFFFF
        return coherence

    def detect_coherence_drift(self, transport_type: str) -> Optional[Dict]:
        """Detecta drift significativo de coerência para um transporte."""
        if transport_type not in self.records or len(self.records[transport_type]) < 20:
            return None

        recent = [r.coherence_score for r in self.records[transport_type][-20:]]
        baseline = self.baselines.get(transport_type, 0.7)

        current_avg = statistics.mean(recent)
        drift = abs(current_avg - baseline)

        if drift > self.drift_threshold:
            return {
                'transport_type': transport_type,
                'baseline': baseline,
                'current_avg': current_avg,
                'drift': drift,
                'threshold': self.drift_threshold,
                'recommendation': 'fallback' if drift > self.drift_threshold * 1.5 else 'monitor',
            }
        return None

    def get_transport_stats(self, transport_type: str) -> Dict:
        """Retorna estatísticas de coerência para um transporte."""
        if transport_type not in self.records or not self.records[transport_type]:
            return {'error': 'No data available'}

        records = list(self.records[transport_type])
        coherence_scores = [r.coherence_score for r in records]

        return {
            'count': len(records),
            'success_rate': sum(1 for r in records if r.success) / len(records),
            'coherence': {
                'mean': statistics.mean(coherence_scores),
                'median': statistics.median(coherence_scores),
                'std': statistics.stdev(coherence_scores) if len(coherence_scores) > 1 else 0,
                'min': min(coherence_scores),
                'max': max(coherence_scores),
            },
            'baseline': self.baselines.get(transport_type),
            'recent_drift': self.detect_coherence_drift(transport_type),
        }

    def get_all_stats(self) -> Dict[str, Dict]:
        """Retorna estatísticas para todos os transportes."""
        return {t: self.get_transport_stats(t) for t in self.records}