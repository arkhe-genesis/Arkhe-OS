# src/cathedral/fundamental/cross_foliation_validator.py
"""
Cross-Foliation Causal Invariance Validator: Testa se a hipótese refinada
mantém invariância causal sob múltiplas transformações de foliação,
validando sua robustez como candidata a regra fundamental.
"""

import asyncio
import numpy as np
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class FoliationTransformation:
    """Representa uma transformação de foliação para teste de invariância."""
    transformation_id: str
    source_foliation: str  # Tipo de foliação de origem
    target_foliation: str  # Tipo de foliação de destino
    transformation_parameters: Dict  # Parâmetros específicos da transformação
    expected_invariants: List[str]  # Quantidades que devem permanecer invariantes

@dataclass
class InvarianceTestResult:
    """Resultado de um teste de invariância causal."""
    test_id: str
    hypothesis_rule: str
    transformation: FoliationTransformation
    invariant_quantities: Dict[str, Tuple[float, float]]  # {quantity: (original_value, transformed_value)}
    deviation_metrics: Dict[str, float]  # Desvios relativos para cada quantidade
    max_deviation: float  # Maior desvio observado
    statistical_significance: float  # p-value para teste de invariância
    invariance_held: bool  # Se invariância foi mantida dentro de tolerância
    timestamp_ns: int

class CrossFoliationCausalInvarianceValidator:
    """Validador de invariância causal cruzada para hipóteses de regras fundamentais."""

    def __init__(self, codex, causal_graph_engine):
        self.codex = codex
        self.causal_engine = causal_graph_engine
        self.test_results: List[InvarianceTestResult] = []

    async def validate_hypothesis_cross_foliation(
        self,
        hypothesis,
        tolerance: float = 1e-6
    ) -> Dict:
        """
        Valida invariância causal da hipótese refinada sob múltiplas transformações de foliação.

        Args:
            hypothesis: Hipótese refinada a ser validada
            tolerance: Tolerância máxima para desvios de quantidades invariantes

        Returns:
            Dict com resultados consolidados da validação
        """

        result = {
            "validation_successful": False,
            "hypothesis_id": hypothesis.hypothesis_id,
            "transformations_tested": 0,
            "invariance_rate": 0.0,
            "max_deviation_observed": 0.0,
            "average_statistical_significance": 0.0,
            "errors": []
        }

        try:
            # 1. Definir conjunto de transformações de foliação para teste
            transformations = await self._define_test_transformations()
            result["transformations_tested"] = len(transformations)

            # 2. Executar testes de invariância para cada transformação
            test_results = []
            for transformation in transformations:
                test_result = await self._execute_invariance_test(
                    hypothesis.rule_definition,
                    transformation,
                    tolerance
                )
                test_results.append(test_result)
                self.test_results.append(test_result)

            # 3. Calcular métricas consolidadas
            invariance_count = sum(1 for t in test_results if t.invariance_held)
            result["invariance_rate"] = invariance_count / len(test_results)
            result["max_deviation_observed"] = max(t.max_deviation for t in test_results)
            result["average_statistical_significance"] = np.mean([t.statistical_significance for t in test_results])

            # 4. Determinar sucesso da validação
            # Critérios: invariância mantida em >95% dos testes E desvio máximo < tolerance
            validation_successful = (
                result["invariance_rate"] >= 0.95 and
                result["max_deviation_observed"] < tolerance
            )
            result["validation_successful"] = bool(validation_successful)

            # 5. Ancorar resultados no Códice
            await self._anchor_validation_results(result, test_results)

            print(f"🌀 Validação causal cruzada concluída: {hypothesis.hypothesis_id}")
            print(f"   • Transformações testadas: {len(transformations)}")
            print(f"   • Taxa de invariância: {result['invariance_rate']*100:.1f}%")
            print(f"   • Desvio máximo: {result['max_deviation_observed']:.2e}")
            print(f"   • Validação {'APROVADA' if validation_successful else 'REPROVADA'}")

        except Exception as e:
            result["errors"].append(f"Cross-foliation validation exception: {str(e)}")

        return result

    async def _define_test_transformations(self) -> List[FoliationTransformation]:
        """Define conjunto de transformações de foliação para testes de invariância."""
        transformations = []

        # Transformação 1: Temporal padrão → Ponderada por coerência
        transformations.append(FoliationTransformation(
            transformation_id="temporal_to_coherence",
            source_foliation="standard_time_foliation",
            target_foliation="coherence_weighted_foliation",
            transformation_parameters={
                "weighting_function": "coherence^2",
                "temporal_resolution_ns": 500,
                "spatial_granularity_km": 1.0
            },
            expected_invariants=["causal_components_count", "max_causal_depth", "causal_edge_density"]
        ))

        # Transformação 2: Ponderada por coerência → Baseada em densidade energética
        transformations.append(FoliationTransformation(
            transformation_id="coherence_to_energy",
            source_foliation="coherence_weighted_foliation",
            target_foliation="energy_density_foliation",
            transformation_parameters={
                "weighting_function": "energy_density",
                "temporal_resolution_ns": 2000,
                "spatial_granularity_km": 50.0
            },
            expected_invariants=["causal_components_count", "max_causal_depth", "causal_degree_entropy"]
        ))

        return transformations

    async def _execute_invariance_test(
        self,
        rule_definition: str,
        transformation: FoliationTransformation,
        tolerance: float
    ) -> InvarianceTestResult:
        """Executa teste de invariância causal para uma transformação específica."""

        # 1. Gerar grafo causal na foliação de origem usando a regra refinada
        causal_graph_original = await self.causal_engine.build_causal_graph_from_rule(
            rule_definition,
            transformation.source_foliation,
            transformation.transformation_parameters
        )

        # 2. Aplicar transformação para obter grafo na foliação de destino
        causal_graph_transformed = await self.causal_engine.transform_causal_graph_foliation(
            causal_graph_original,
            transformation.source_foliation,
            transformation.target_foliation,
            transformation.transformation_parameters
        )

        # 3. Extrair quantidades invariantes de ambos os grafos
        invariant_quantities = {}
        for quantity in transformation.expected_invariants:
            original_value = await self.causal_engine.extract_causal_invariant(causal_graph_original, quantity)
            transformed_value = await self.causal_engine.extract_causal_invariant(causal_graph_transformed, quantity)
            invariant_quantities[quantity] = (float(original_value), float(transformed_value))

        # 4. Calcular desvios relativos para cada quantidade
        deviation_metrics = {}
        for quantity, (orig, trans) in invariant_quantities.items():
            if abs(orig) > 1e-10:  # Evitar divisão por zero
                deviation = abs(trans - orig) / abs(orig)
            else:
                deviation = abs(trans - orig)  # Desvio absoluto se valor próximo de zero
            deviation_metrics[f"{quantity}_deviation"] = float(deviation)

        # 5. Determinar desvio máximo
        max_deviation = max(deviation_metrics.values()) if deviation_metrics else 0.0

        # 6. Testar significância estatística dos desvios
        statistical_significance = await self._test_invariance_significance(deviation_metrics, tolerance)

        # 7. Determinar se invariância foi mantida
        invariance_held = all(dev < tolerance for dev in deviation_metrics.values())

        # 8. Criar resultado do teste
        test_result = InvarianceTestResult(
            test_id=f"invariance_test_{transformation.transformation_id}_{int(time.time())}",
            hypothesis_rule=rule_definition,
            transformation=transformation,
            invariant_quantities=invariant_quantities,
            deviation_metrics=deviation_metrics,
            max_deviation=float(max_deviation),
            statistical_significance=float(statistical_significance),
            invariance_held=bool(invariance_held),
            timestamp_ns=time.time_ns()
        )

        return test_result

    async def _test_invariance_significance(self, deviation_metrics: Dict[str, float],
                                          tolerance: float) -> float:
        """Testa significância estatística dos desvios observados."""
        # Em produção: teste de permutação ou bootstrap para avaliar se desvios são compatíveis com ruído
        # Para simulação: p-value baseado na magnitude dos desvios relativos à tolerância

        if not deviation_metrics:
            return 1.0

        max_deviation = max(deviation_metrics.values())

        # P-value menor para desvios maiores em relação à tolerância
        relative_deviation = max_deviation / max(1e-10, tolerance)
        p_value = np.exp(-relative_deviation * 10)  # Decaimento exponencial

        return float(min(1.0, max(1e-300, p_value)))  # Limitar para evitar underflow

    async def _anchor_validation_results(self, result: Dict, test_results: List[InvarianceTestResult]):
        """Ancora resultados da validação no Códice."""
        await self.codex.store_artifact(
            artifact_id=f"cross_foliation_validation_{result['hypothesis_id']}_{int(time.time())}",
            content_hash=hashlib.sha256(json.dumps({
                "hypothesis_id": result["hypothesis_id"],
                "transformations_tested": result["transformations_tested"],
                "invariance_rate": result["invariance_rate"],
                "max_deviation_observed": result["max_deviation_observed"],
                "average_statistical_significance": result["average_statistical_significance"],
                "validation_successful": result["validation_successful"]
            }, sort_keys=True, default=str).encode()).hexdigest(),
            metadata={
                "type": "cross_foliation_causal_invariance_validation",
                "hypothesis_id": result["hypothesis_id"],
                "invariance_rate": result["invariance_rate"],
                "validation_successful": result["validation_successful"]
            }
        )
