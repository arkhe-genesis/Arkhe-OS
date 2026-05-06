#!/usr/bin/env python3
"""
federated_metric_aggregator.py — Agregação federada de métricas cósmicas
com privacidade diferencial e verificação criptográfica.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import hashlib
import logging
from collections import defaultdict

class AggregationStrategy(Enum):
    """Estratégias de agregação federada."""
    WEIGHTED_AVERAGE = auto()  # Média ponderada por confiança do nó
    MEDIAN = auto()            # Mediana para robustez a outliers
    TRIMMED_MEAN = auto()      # Média aparada (remove extremos)
    BAYESIAN_FUSION = auto()   # Fusão bayesiana com priors cósmicos
    DP_AGGREGATE = auto()      # Agregação com privacidade diferencial

@dataclass
class LocalMetricObservation:
    """Observação local de métrica para agregação federada."""
    metric_name: str
    local_value: float
    local_confidence: float  # [0, 1] — confiança na medição local
    node_id: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    differential_privacy_epsilon: Optional[float] = None  # ε para DP se aplicado

    def add_noise_dp(self, sensitivity: float, epsilon: float) -> 'LocalMetricObservation':
        """Adiciona ruído de Laplace para privacidade diferencial."""
        if epsilon <= 0:
            return self

        # Ruído de Laplace: scale = sensitivity / epsilon
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)

        return LocalMetricObservation(
            metric_name=self.metric_name,
            local_value=self.local_value + noise,
            local_confidence=self.local_confidence,
            node_id=self.node_id,
            timestamp=self.timestamp,
            metadata={**self.metadata, 'dp_noise_added': True, 'dp_epsilon': epsilon},
            differential_privacy_epsilon=epsilon
        )

@dataclass
class FederatedMetricResult:
    """Resultado da agregação federada de métrica."""
    metric_name: str
    aggregated_value: float
    confidence_interval: Tuple[float, float]  # [lower, upper] com 95% confiança
    contributing_nodes: List[str]
    aggregation_strategy: AggregationStrategy
    timestamp: float
    privacy_guarantee: Optional[Dict[str, float]] = None  # ε, δ se DP aplicado
    consensus_verified: bool = False

    def to_dict(self) -> Dict:
        return {
            'metric_name': self.metric_name,
            'aggregated_value': self.aggregated_value,
            'confidence_interval': self.confidence_interval,
            'contributing_nodes': self.contributing_nodes,
            'aggregation_strategy': self.aggregation_strategy.name,
            'timestamp': self.timestamp,
            'privacy_guarantee': self.privacy_guarantee,
            'consensus_verified': self.consensus_verified
        }

class FederatedMetricAggregator:
    """
    Agregador federado de métricas cósmicas com suporte a múltiplas estratégias
    e privacidade diferencial opcional.
    """

    def __init__(
        self,
        node_id: str,
        default_strategy: AggregationStrategy = AggregationStrategy.WEIGHTED_AVERAGE,
        dp_enabled: bool = True,
        default_dp_epsilon: float = 1.0,
        min_contributors: int = 3,
        consensus_protocol: Optional['CosmicConsensusProtocol'] = None
    ):
        self.node_id = node_id
        self.default_strategy = default_strategy
        self.dp_enabled = dp_enabled
        self.default_dp_epsilon = default_dp_epsilon
        self.min_contributors = min_contributors
        self.consensus_protocol = consensus_protocol

        # Buffer de observações locais pendentes para agregação
        self.local_observations: Dict[str, List[LocalMetricObservation]] = defaultdict(list)

        # Resultados federados cacheados
        self.federated_results: Dict[str, FederatedMetricResult] = {}

        # Pesos de confiança por nó (aprendidos ou configurados)
        self.node_confidence_weights: Dict[str, float] = defaultdict(lambda: 1.0)

        # Sensibilidades das métricas para privacidade diferencial
        self.metric_sensitivities: Dict[str, float] = {
            'cosmic.phi_c_global': 0.1,
            'cosmic.entanglement_health': 0.15,
            'operations.response_time_p99': 100.0,  # ms
            'security.anomaly_rate': 0.05,
            # Adicionar mais métricas conforme necessário
        }

        # Callbacks para notificação de novos resultados federados
        self.aggregation_callbacks: List[Callable] = []

        logging.info(f"✅ FederatedMetricAggregator initialized: node={node_id}, dp={dp_enabled}")

    def submit_local_observation(
        self,
        metric_name: str,
        local_value: float,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> LocalMetricObservation:
        """Submete observação local para futura agregação federada."""
        observation = LocalMetricObservation(
            metric_name=metric_name,
            local_value=local_value,
            local_confidence=confidence,
            node_id=self.node_id,
            timestamp=time.time(),
            metadata=metadata or {}
        )

        # Aplicar privacidade diferencial se habilitado
        if self.dp_enabled and metric_name in self.metric_sensitivities:
            sensitivity = self.metric_sensitivities[metric_name]
            epsilon = metadata.get('dp_epsilon', self.default_dp_epsilon) if metadata else self.default_dp_epsilon
            observation = observation.add_noise_dp(sensitivity, epsilon)

        # Armazenar observação
        self.local_observations[metric_name].append(observation)

        # Manter buffer limitado
        if len(self.local_observations[metric_name]) > 100:
            self.local_observations[metric_name] = self.local_observations[metric_name][-50:]

        return observation

    async def aggregate_federated_metric(
        self,
        metric_name: str,
        strategy: Optional[AggregationStrategy] = None,
        require_consensus: bool = True,
        timeout_sec: float = 30.0
    ) -> Optional[FederatedMetricResult]:
        """
        Agrega métrica federada coletando observações de múltiplos observatórios.

        Args:
            metric_name: Nome da métrica a agregar
            strategy: Estratégia de agregação (usa default se None)
            require_consensus: Se requer consenso antes de retornar resultado
            timeout_sec: Timeout para coleta de observações

        Returns:
            FederatedMetricResult ou None se agregação falhar
        """
        strategy = strategy or self.default_strategy
        start_time = time.time()

        # Coletar observações de outros nós (simulado)
        # Em produção: solicitar via protocolo P2P da federação
        remote_observations = await self._collect_remote_observations(
            metric_name, timeout_sec=timeout_sec
        )

        # Combinar com observações locais
        all_observations = self.local_observations.get(metric_name, []) + remote_observations

        # Verificar mínimo de contribuidores
        if len(all_observations) < self.min_contributors:
            logging.warning(f"⚠️ Insufficient contributors for {metric_name}: {len(all_observations)} < {self.min_contributors}")
            return None

        # Executar agregação baseada na estratégia
        if strategy == AggregationStrategy.WEIGHTED_AVERAGE:
            result = self._aggregate_weighted_average(metric_name, all_observations)
        elif strategy == AggregationStrategy.MEDIAN:
            result = self._aggregate_median(metric_name, all_observations)
        elif strategy == AggregationStrategy.TRIMMED_MEAN:
            result = self._aggregate_trimmed_mean(metric_name, all_observations)
        elif strategy == AggregationStrategy.BAYESIAN_FUSION:
            result = self._aggregate_bayesian_fusion(metric_name, all_observations)
        elif strategy == AggregationStrategy.DP_AGGREGATE:
            result = self._aggregate_dp(metric_name, all_observations)
        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")

        # Verificar consenso se requerido
        if require_consensus and self.consensus_protocol:
            # Submeter resultado para consenso federado
            consensus_result = await self._verify_via_consensus(result)
            result.consensus_verified = consensus_result

        # Cache do resultado
        self.federated_results[metric_name] = result

        # Notificar callbacks
        for callback in self.aggregation_callbacks:
            try:
                callback(result.to_dict())
            except Exception as e:
                logging.error(f"⚠️ Aggregation callback error: {e}")

        logging.info(f"✅ Agregação federada concluída: {metric_name} = {result.aggregated_value:.4f}")
        return result

    async def _collect_remote_observations(
        self,
        metric_name: str,
        timeout_sec: float
    ) -> List[LocalMetricObservation]:
        """Coleta observações remotas de outros observatórios (simulado)."""
        # Em produção: enviar solicitação P2P para validadores da federação
        # e aguardar respostas assinadas

        # Simulação: gerar observações sintéticas baseadas em distribuição conhecida
        observations = []
        num_validators = 5  # Simular 5 outros validadores

        for i in range(num_validators):
            # Valor base com variação controlada
            base_value = 0.85  # Valor "verdadeiro" simulado para Φ_C
            noise = np.random.normal(0, 0.03)  # Ruído de medição
            node_confidence = np.random.uniform(0.7, 1.0)

            obs = LocalMetricObservation(
                metric_name=metric_name,
                local_value=base_value + noise,
                local_confidence=node_confidence,
                node_id=f"validator_{i}",
                timestamp=time.time(),
                metadata={'simulated': True}
            )

            # Aplicar DP se habilitado
            if self.dp_enabled and metric_name in self.metric_sensitivities:
                sensitivity = self.metric_sensitivities[metric_name]
                obs = obs.add_noise_dp(sensitivity, self.default_dp_epsilon)

            observations.append(obs)

        # Simular latência de rede
        await asyncio.sleep(min(timeout_sec / 10, 0.1))

        return observations

    def _aggregate_weighted_average(
        self,
        metric_name: str,
        observations: List[LocalMetricObservation]
    ) -> FederatedMetricResult:
        """Agregação por média ponderada por confiança."""
        values = np.array([obs.local_value for obs in observations])
        weights = np.array([
            obs.local_confidence * self.node_confidence_weights.get(obs.node_id, 1.0)
            for obs in observations
        ])

        # Normalizar pesos
        weights = weights / weights.sum()

        # Média ponderada
        aggregated = np.sum(values * weights)

        # Intervalo de confiança (aproximação)
        std_err = np.sqrt(np.sum(weights**2 * np.var(values)))
        ci_lower = aggregated - 1.96 * std_err
        ci_upper = aggregated + 1.96 * std_err

        # Privacidade: calcular ε agregado se DP aplicado
        privacy_guarantee = None
        dp_epsilons = [obs.differential_privacy_epsilon for obs in observations if obs.differential_privacy_epsilon]
        if dp_epsilons:
            # Composição básica de DP: ε_total = sum(ε_i)
            privacy_guarantee = {
                'epsilon_total': sum(dp_epsilons),
                'delta': 1e-5  # δ padrão
            }

        return FederatedMetricResult(
            metric_name=metric_name,
            aggregated_value=float(aggregated),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            contributing_nodes=[obs.node_id for obs in observations],
            aggregation_strategy=AggregationStrategy.WEIGHTED_AVERAGE,
            timestamp=time.time(),
            privacy_guarantee=privacy_guarantee
        )

    def _aggregate_median(
        self,
        metric_name: str,
        observations: List[LocalMetricObservation]
    ) -> FederatedMetricResult:
        """Agregação por mediana (robusta a outliers)."""
        values = np.array([obs.local_value for obs in observations])
        aggregated = np.median(values)

        # Intervalo de confiança via bootstrap (simplificado)
        ci_lower = np.percentile(values, 2.5)
        ci_upper = np.percentile(values, 97.5)

        return FederatedMetricResult(
            metric_name=metric_name,
            aggregated_value=float(aggregated),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            contributing_nodes=[obs.node_id for obs in observations],
            aggregation_strategy=AggregationStrategy.MEDIAN,
            timestamp=time.time()
        )

    def _aggregate_trimmed_mean(
        self,
        metric_name: str,
        observations: List[LocalMetricObservation],
        trim_fraction: float = 0.1
    ) -> FederatedMetricResult:
        """Agregação por média aparada (remove extremos)."""
        values = np.array([obs.local_value for obs in observations])

        # Ordenar e remover fração dos extremos
        sorted_values = np.sort(values)
        n = len(sorted_values)
        trim_count = int(n * trim_fraction)

        trimmed = sorted_values[trim_count:n - trim_count] if trim_count > 0 else sorted_values
        aggregated = np.mean(trimmed)

        # Intervalo de confiança
        std_err = np.std(trimmed) / np.sqrt(len(trimmed))
        ci_lower = aggregated - 1.96 * std_err
        ci_upper = aggregated + 1.96 * std_err

        return FederatedMetricResult(
            metric_name=metric_name,
            aggregated_value=float(aggregated),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            contributing_nodes=[obs.node_id for obs in observations],
            aggregation_strategy=AggregationStrategy.TRIMMED_MEAN,
            timestamp=time.time()
        )

    def _aggregate_bayesian_fusion(
        self,
        metric_name: str,
        observations: List[LocalMetricObservation]
    ) -> FederatedMetricResult:
        """Agregação por fusão bayesiana com prior cósmico."""
        # Prior cósmico para Φ_C: Beta(α=8, β=2) → média 0.8
        if metric_name == 'cosmic.phi_c_global':
            prior_alpha, prior_beta = 8.0, 2.0
        else:
            # Prior não-informativo para outras métricas
            prior_alpha, prior_beta = 1.0, 1.0

        # Atualizar prior com observações (modelo Beta-Binomial simplificado)
        # Para métricas contínuas, usar aproximação Gaussiana
        values = np.array([obs.local_value for obs in observations])
        confidences = np.array([obs.local_confidence for obs in observations])

        # Média e variância ponderadas
        weighted_mean = np.sum(values * confidences) / np.sum(confidences)
        weighted_var = np.sum(confidences * (values - weighted_mean)**2) / np.sum(confidences)

        # Fusão bayesiana: posterior = prior + likelihood
        # Simplificação: combinar prior Gaussiano com likelihood Gaussiana
        prior_mean = prior_alpha / (prior_alpha + prior_beta)
        prior_var = (prior_alpha * prior_beta) / ((prior_alpha + prior_beta)**2 * (prior_alpha + prior_beta + 1))

        # Posterior parameters
        posterior_var = 1 / (1/prior_var + np.sum(confidences) / weighted_var)
        posterior_mean = posterior_var * (prior_mean/prior_var + np.sum(confidences * values) / weighted_var)

        aggregated = posterior_mean
        ci_lower = aggregated - 1.96 * np.sqrt(posterior_var)
        ci_upper = aggregated + 1.96 * np.sqrt(posterior_var)

        return FederatedMetricResult(
            metric_name=metric_name,
            aggregated_value=float(aggregated),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            contributing_nodes=[obs.node_id for obs in observations],
            aggregation_strategy=AggregationStrategy.BAYESIAN_FUSION,
            timestamp=time.time()
        )

    def _aggregate_dp(
        self,
        metric_name: str,
        observations: List[LocalMetricObservation]
    ) -> FederatedMetricResult:
        """Agregação com privacidade diferencial garantida."""
        # Usar mecanismo de média com ruído de Laplace
        values = np.array([obs.local_value for obs in observations])

        # Média simples (já com ruído DP nas observações individuais)
        aggregated = np.mean(values)

        # Calcular ε agregado via composição avançada
        dp_epsilons = [obs.differential_privacy_epsilon for obs in observations if obs.differential_privacy_epsilon]
        if dp_epsilons:
            # Advanced composition: ε_total ≈ √(2k ln(1/δ))·ε + kε(e^ε - 1)
            k = len(dp_epsilons)
            delta = 1e-5
            avg_epsilon = np.mean(dp_epsilons)
            term1 = np.sqrt(2 * k * np.log(1/delta)) * avg_epsilon
            term2 = k * avg_epsilon * (np.exp(avg_epsilon) - 1)
            epsilon_total = term1 + term2

            privacy_guarantee = {
                'epsilon_total': float(epsilon_total),
                'delta': delta,
                'composition_method': 'advanced'
            }
        else:
            privacy_guarantee = None

        # Intervalo de confiança (conservativo devido ao ruído DP)
        std_with_dp = np.std(values) + (self.metric_sensitivities.get(metric_name, 1.0) * self.default_dp_epsilon)
        ci_lower = aggregated - 2.58 * std_with_dp  # 99% CI para compensar ruído DP
        ci_upper = aggregated + 2.58 * std_with_dp

        return FederatedMetricResult(
            metric_name=metric_name,
            aggregated_value=float(aggregated),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            contributing_nodes=[obs.node_id for obs in observations],
            aggregation_strategy=AggregationStrategy.DP_AGGREGATE,
            timestamp=time.time(),
            privacy_guarantee=privacy_guarantee
        )

    async def _verify_via_consensus(self, result: FederatedMetricResult) -> bool:
        """Verifica resultado de agregação via protocolo de consenso."""
        if not self.consensus_protocol:
            return True

        # Submeter resultado para consenso
        proposal = await self.consensus_protocol.propose_metric(
            metric_name=result.metric_name,
            metric_value=result.aggregated_value,
            metric_metadata={
                'aggregation_strategy': result.aggregation_strategy.name,
                'contributing_nodes': result.contributing_nodes,
                'confidence_interval': result.confidence_interval,
                'privacy_guarantee': result.privacy_guarantee
            }
        )

        # Aguardar decisão (simulado)
        if proposal:
            await asyncio.sleep(0.5)  # Simular tempo de consenso
            return True

        return False

    def register_aggregation_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para novos resultados federados."""
        self.aggregation_callbacks.append(callback)

    def update_node_confidence(self, node_id: str, new_confidence: float):
        """Atualiza peso de confiança para nó específico."""
        self.node_confidence_weights[node_id] = np.clip(new_confidence, 0.0, 1.0)

    def get_federated_result(self, metric_name: str) -> Optional[Dict]:
        """Retorna resultado federado cacheado para métrica."""
        result = self.federated_results.get(metric_name)
        return result.to_dict() if result else None

    def get_aggregator_health(self) -> Dict[str, Any]:
        """Retorna métricas de saúde do agregador federado."""
        return {
            'node_id': self.node_id,
            'local_observations_count': sum(len(obs) for obs in self.local_observations.values()),
            'federated_results_count': len(self.federated_results),
            'dp_enabled': self.dp_enabled,
            'default_strategy': self.default_strategy.name,
            'node_confidence_weights': dict(self.node_confidence_weights),
            'min_contributors': self.min_contributors
        }
