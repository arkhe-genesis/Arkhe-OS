#!/usr/bin/env python3
"""
performance_optimizer.py — Otimização dinâmica de throughput para inferência distribuída
Ajusta: batch sizes, quantização, balanceamento de carga, caching
"""

import torch
import torch.distributed as dist
import numpy as np
import time
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque, defaultdict
import threading
from prometheus_client import Histogram, Counter, Gauge

# Métricas Prometheus para monitoramento em tempo real
BATCH_SIZE_GAUGE = Gauge('arkhe_batch_size_current', 'Current batch size', ['node_rank'])
THROUGHPUT_GAUGE = Gauge('arkhe_throughput_samples_per_sec', 'Samples processed per second', ['node_rank'])
QUANTIZATION_LEVEL_GAUGE = Gauge('arkhe_quantization_level', 'Current quantization (1=FP8, 2=BF16, 3=FP32)', ['node_rank'])
LOAD_BALANCE_GAUGE = Gauge('arkhe_worker_load', 'Relative load per worker', ['node_rank'])

@dataclass
class PerformanceConfig:
    """Configurações de otimização de performance"""
    # Parâmetros de batch dinâmico
    min_batch_size: int = 1
    max_batch_size: int = 32
    batch_growth_factor: float = 1.25
    batch_shrink_factor: float = 0.75
    latency_target_ms: float = 50.0  # Latência alvo por inference
    latency_tolerance: float = 0.2    # Tolerância de 20%

    # Parâmetros de quantização adaptativa
    quantization_levels: Dict[str, Dict] = field(default_factory=lambda: {
        'fp8': {'dtype': torch.float8_e4m3fn if hasattr(torch, 'float8_e4m3fn') else torch.float32, 'speedup': 4.0, 'memory_factor': 0.25},
        'bf16': {'dtype': torch.bfloat16, 'speedup': 2.0, 'memory_factor': 0.5},
        'fp32': {'dtype': torch.float32, 'speedup': 1.0, 'memory_factor': 1.0}
    })
    min_accuracy_threshold: float = 0.95  # Manter 95% da precisão de referência
    accuracy_check_interval: int = 100    # Verificar precisão a cada N batches

    # Parâmetros de balanceamento de carga
    load_check_interval: float = 5.0  # segundos
    rebalance_threshold: float = 0.15  # Rebalancear se carga difere >15%
    migration_cost_estimate: float = 0.1  # Custo estimado de migrar estado entre workers

    # Parâmetros de caching
    cache_max_size: int = 1000  # Máximo de embeddings em cache
    cache_ttl_seconds: float = 300.0  # TTL de 5 minutos
    cache_hit_target: float = 0.3  # Target de 30% cache hits


class PerformanceOptimizer:
    """
    Otimizador dinâmico de performance para inferência neural distribuída.

    Funcionalidades:
    - Ajuste adaptativo de batch size baseado em latência observada
    - Seleção automática de nível de quantização (FP8/BF16/FP32)
    - Balanceamento de carga entre workers via migração de tarefas
    - Caching inteligente de embeddings e resultados intermediários
    """

    def __init__(self, config: PerformanceConfig, rank: int = 0, world_size: int = 1):
        self.config = config
        self.rank = rank
        self.world_size = world_size
        self.is_master = (rank == 0)

        # Estado do otimizador
        self.current_batch_size = config.min_batch_size
        self.current_quantization = 'fp8'  # Começar com máxima eficiência
        self.worker_loads: Dict[int, float] = {i: 1.0 for i in range(world_size)}

        # Histórico para decisões adaptativas
        self.latency_history: deque = deque(maxlen=100)
        self.throughput_history: deque = deque(maxlen=50)
        self.accuracy_samples: List[Tuple[float, float]] = []  # (quant_level, accuracy)

        # Cache LRU para embeddings
        self.embedding_cache: Dict[str, Tuple[torch.Tensor, float]] = {}
        self.cache_access_order: deque = deque(maxlen=config.cache_max_size)

        # Lock para thread-safety em operações de cache
        self.cache_lock = threading.RLock()

        # Métricas acumuladas
        self.total_processed = 0
        self.total_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

        # Atualizar métricas Prometheus iniciais
        self._update_metrics()

        if self.is_master:
            print(f"🎛️ PerformanceOptimizer initialized: batch={self.current_batch_size}, quant={self.current_quantization}")

    def optimize_batch_size(self, observed_latency_ms: float) -> int:
        """
        Ajusta batch size baseado na latência observada vs. target.

        Estratégia:
        - Se latência < target * (1 - tolerance): aumentar batch
        - Se latência > target * (1 + tolerance): diminuir batch
        - Manter dentro de [min_batch_size, max_batch_size]
        """
        self.latency_history.append(observed_latency_ms)

        # Calcular média móvel das últimas 10 medições
        if len(self.latency_history) >= 10:
            avg_latency = np.mean(list(self.latency_history)[-10:])
        else:
            avg_latency = observed_latency_ms

        # Decidir ajuste
        if avg_latency < self.config.latency_target_ms * (1 - self.config.latency_tolerance):
            # Latência boa, podemos aumentar batch
            new_batch = min(
                self.config.max_batch_size,
                int(self.current_batch_size * self.config.batch_growth_factor)
            )
        elif avg_latency > self.config.latency_target_ms * (1 + self.config.latency_tolerance):
            # Latência alta, reduzir batch
            new_batch = max(
                self.config.min_batch_size,
                int(self.current_batch_size * self.config.batch_shrink_factor)
            )
        else:
            # Dentro da tolerância, manter atual
            new_batch = self.current_batch_size

        # Aplicar mudança se diferente
        if new_batch != self.current_batch_size:
            print(f"📊 Adjusting batch size: {self.current_batch_size} → {new_batch} (latency: {avg_latency:.2f}ms)")
            self.current_batch_size = new_batch
            BATCH_SIZE_GAUGE.labels(node_rank=str(self.rank)).set(new_batch)

        return self.current_batch_size

    def select_quantization_level(self, accuracy_estimate: Optional[float] = None) -> str:
        """
        Seleciona nível de quantização baseado em trade-off velocidade/precisão.

        Estratégia:
        - Começar com FP8 (máxima velocidade)
        - Se accuracy_estimate < threshold, degradar para BF16, depois FP32
        - Periodicamente testar níveis mais eficientes para verificar se ainda são viáveis
        """
        if accuracy_estimate is not None:
            self.accuracy_samples.append((self._quant_to_numeric(self.current_quantization), accuracy_estimate))

            # Verificar se precisamos degradar quantização
            if len(self.accuracy_samples) >= 10:
                recent_accuracy = np.mean([acc for _, acc in self.accuracy_samples[-10:]])

                if recent_accuracy < self.config.min_accuracy_threshold:
                    # Degradar para nível menos agressivo
                    if self.current_quantization == 'fp8':
                        new_quant = 'bf16'
                    elif self.current_quantization == 'bf16':
                        new_quant = 'fp32'
                    else:
                        new_quant = 'fp32'  # Já está no máximo

                    if new_quant != self.current_quantization:
                        print(f"🎚️ Degrading quantization: {self.current_quantization} → {new_quant} (accuracy: {recent_accuracy:.3f})")
                        self.current_quantization = new_quant
                        QUANTIZATION_LEVEL_GAUGE.labels(node_rank=str(self.rank)).set(self._quant_to_numeric(new_quant))

        # Periodicamente tentar upgrade (apenas no master)
        if self.is_master and self.total_processed % self.config.accuracy_check_interval == 0:
            self._try_quantization_upgrade()

        return self.current_quantization

    def _quant_to_numeric(self, quant: str) -> float:
        """Mapeia nível de quantização para valor numérico (para métricas)"""
        mapping = {'fp8': 1.0, 'bf16': 2.0, 'fp32': 3.0}
        return mapping.get(quant, 2.0)

    def _try_quantization_upgrade(self):
        """Tenta upgrade para nível de quantização mais eficiente"""
        if self.current_quantization == 'fp32':
            candidate = 'bf16'
        elif self.current_quantization == 'bf16':
            candidate = 'fp8'
        else:
            return  # Já está no máximo

        # Em produção: rodar inference de teste com candidate e medir accuracy
        # Aqui: simular decisão baseada em histórico
        if len(self.accuracy_samples) >= 20:
            # Se accuracy média está bem acima do threshold, podemos tentar upgrade
            avg_accuracy = np.mean([acc for _, acc in self.accuracy_samples[-20:]])
            if avg_accuracy > self.config.min_accuracy_threshold + 0.03:  # 3% de margem
                print(f"🎚️ Attempting quantization upgrade: {self.current_quantization} → {candidate}")
                self.current_quantization = candidate
                QUANTIZATION_LEVEL_GAUGE.labels(node_rank=str(self.rank)).set(self._quant_to_numeric(candidate))

    def balance_load(self, local_queue_size: int) -> Optional[Dict]:
        """
        Balanceia carga entre workers via migração de tarefas.

        Retorna dict com tarefa para migrar (se necessário), ou None.
        """
        if self.world_size <= 1:
            return None

        # Coletar cargas de todos os workers via all_gather
        local_load = torch.tensor([float(local_queue_size)], device='cuda' if torch.cuda.is_available() else 'cpu')
        all_loads = [torch.zeros_like(local_load) for _ in range(self.world_size)]

        if dist.is_initialized():
            dist.all_gather(all_loads, local_load)
            loads = [t.item() for t in all_loads]
        else:
            loads = [local_load.item()] * self.world_size

        # Atualizar métricas
        for i, load in enumerate(loads):
            LOAD_BALANCE_GAUGE.labels(node_rank=str(i)).set(load)

        # Calcular estatísticas de carga
        avg_load = np.mean(loads)
        max_load = np.max(loads)

        # Decidir se precisa rebalancear
        if max_load > avg_load * (1 + self.config.rebalance_threshold):
            # Este worker está sobrecarregado?
            if loads[self.rank] == max_load:
                # Encontrar worker menos carregado
                min_worker = int(np.argmin(loads))
                if min_worker != self.rank:
                    # Preparar migração de uma tarefa
                    migration_task = {
                        'from_rank': self.rank,
                        'to_rank': min_worker,
                        'estimated_cost': self.config.migration_cost_estimate,
                        'timestamp': time.time()
                    }
                    print(f"⚖️ Load balancing: migrating task from rank {self.rank} → {min_worker}")
                    return migration_task

        return None

    def cache_embedding(self, signal_hash: str, embedding: torch.Tensor) -> bool:
        """
        Armazena embedding no cache LRU.

        Retorna True se inserido, False se cache cheio e item evitado.
        """
        with self.cache_lock:
            # Remover item mais antigo se cache cheio
            if len(self.embedding_cache) >= self.config.cache_max_size and signal_hash not in self.embedding_cache:
                if self.cache_access_order:
                    oldest = self.cache_access_order.popleft()
                    if oldest in self.embedding_cache:
                        del self.embedding_cache[oldest]

            # Inserir novo item
            self.embedding_cache[signal_hash] = (embedding.clone().cpu(), time.time())
            self.cache_access_order.append(signal_hash)
            return True

    def get_cached_embedding(self, signal_hash: str) -> Optional[torch.Tensor]:
        """
        Recupera embedding do cache se disponível e não expirado.

        Retorna tensor ou None se cache miss/expired.
        """
        with self.cache_lock:
            if signal_hash not in self.embedding_cache:
                self.cache_misses += 1
                return None

            embedding, timestamp = self.embedding_cache[signal_hash]

            # Verificar TTL
            if time.time() - timestamp > self.config.cache_ttl_seconds:
                del self.embedding_cache[signal_hash]
                if signal_hash in self.cache_access_order:
                    self.cache_access_order.remove(signal_hash)
                self.cache_misses += 1
                return None

            # Cache hit: atualizar ordem de acesso
            if signal_hash in self.cache_access_order:
                self.cache_access_order.remove(signal_hash)
            self.cache_access_order.append(signal_hash)
            self.cache_hits += 1

            return embedding.to('cuda' if torch.cuda.is_available() else 'cpu')

    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas de cache para monitoramento"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0.0

        return {
            'cache_size': len(self.embedding_cache),
            'cache_max_size': self.config.cache_max_size,
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate,
            'target_hit_rate': self.config.cache_hit_target
        }

    def record_inference(self, duration_ms: float, batch_size: int, quantization: str):
        """Registra métricas de uma inference completada"""
        self.total_processed += batch_size
        self.total_time += duration_ms / 1000.0  # converter para segundos

        # Calcular throughput instantâneo
        if self.total_time > 0:
            throughput = self.total_processed / self.total_time
            self.throughput_history.append(throughput)
            THROUGHPUT_GAUGE.labels(node_rank=str(self.rank)).set(throughput)

    def get_optimization_report(self) -> Dict:
        """Gera relatório consolidado de otimização"""
        cache_stats = self.get_cache_stats()

        return {
            'rank': self.rank,
            'current_config': {
                'batch_size': self.current_batch_size,
                'quantization': self.current_quantization,
                'latency_target_ms': self.config.latency_target_ms
            },
            'performance': {
                'total_processed': self.total_processed,
                'total_time_sec': self.total_time,
                'avg_throughput': self.total_processed / self.total_time if self.total_time > 0 else 0,
                'recent_throughput': np.mean(list(self.throughput_history)[-10:]) if self.throughput_history else 0
            },
            'cache': cache_stats,
            'load_balance': {
                'my_load': self.worker_loads.get(self.rank, 1.0),
                'avg_load': np.mean(list(self.worker_loads.values())),
                'imbalance_ratio': max(self.worker_loads.values()) / min(self.worker_loads.values()) if self.worker_loads.values() else 1.0
            },
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações de otimização baseadas no estado atual"""
        recommendations = []

        # Recomendações de batch size
        if self.current_batch_size < self.config.max_batch_size and len(self.latency_history) >= 10:
            avg_latency = np.mean(list(self.latency_history)[-10:])
            if avg_latency < self.config.latency_target_ms * 0.8:
                recommendations.append(f"Consider increasing batch_size to {min(self.config.max_batch_size, int(self.current_batch_size * 1.5))} for higher throughput")

        # Recomendações de quantização
        if self.current_quantization != 'fp8' and len(self.accuracy_samples) >= 20:
            avg_acc = np.mean([acc for _, acc in self.accuracy_samples[-20:]])
            if avg_acc > self.config.min_accuracy_threshold + 0.05:
                recommendations.append("Accuracy margin allows testing FP8 quantization for 2-4x speedup")

        # Recomendações de cache
        cache_stats = self.get_cache_stats()
        if cache_stats['hit_rate'] < self.config.cache_hit_target * 0.5:
            recommendations.append(f"Cache hit rate ({cache_stats['hit_rate']:.1%}) below target; consider increasing cache_ttl or cache_max_size")

        return recommendations

    def _update_metrics(self):
        """Atualiza métricas Prometheus com estado atual"""
        BATCH_SIZE_GAUGE.labels(node_rank=str(self.rank)).set(self.current_batch_size)
        QUANTIZATION_LEVEL_GAUGE.labels(node_rank=str(self.rank)).set(self._quant_to_numeric(self.current_quantization))
