#!/usr/bin/env python3
"""
Substrato 198-F: Neurogenetic Experimental Pipeline
Integra RNA-Seq calibration, optogenetics hardware, expanded gene map,
e nonlinear GRN simulation em pipeline único para validação experimental.
"""
import asyncio
import json
import time
import hashlib
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import logging

from validation.rnaseq_calibration_engine import RNASeqCalibrationEngine
from hardware.optogenetics_platform_adapter import OptogeneticsPlatformAdapter, HardwareConfig, OptogeneticHardware
from models.nonlinear_grn_simulator import NonlinearGRNSimulator, GRNState, GRNInteraction, InteractionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExperimentalConfig:
    """Configuração completa para experimento neurogenético."""
    # Calibração RNA-Seq
    rnaseq_data_dir: str
    reference_studies: List[str]

    # Hardware optogenético
    hardware_type: str
    wavelength_nm: float
    max_power_mw_mm2: float

    # GRN e genes alvo
    semantic_term: str
    target_genes: Dict[str, float]
    grn_interactions: List[GRNInteraction]

    # Parâmetros experimentais
    duration_hours: float
    sampling_interval_minutes: float
    safety_limits: Dict[str, float]

@dataclass
class ExperimentalResult:
    """Resultado consolidado de experimento neurogenético."""
    experiment_id: str
    semantic_term: str
    config_hash: str

    # Resultados de calibração
    calibrated_profile: Dict[str, float]
    calibration_confidence: float

    # Resultados de simulação GRN
    grn_final_state: Dict[str, float]
    grn_convergence_time: float

    # Resultados de hardware
    light_pattern_applied: bool
    safety_violations: int

    # Métricas de sucesso
    alignment_score: float  # Quão próximo do perfil alvo
    reproducibility_score: float  # Consistência entre réplicas

    # Ancoragem
    temporal_seal: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

class NeurogeneticExperimentalPipeline:
    """
    Pipeline unificado para validação experimental do Verbo-Campo.

    Fluxo completo:
    1. Carregar e calibrar mapa gênico com dados RNA-Seq
    2. Configurar hardware optogenético com limites de segurança
    3. Construir GRN não-linear baseada no termo semântico
    4. Simular dinâmica gênica com sinais externos do P2I
    5. Traduzir campo vetorial para padrão de luz executável
    6. Aplicar padrão no hardware com monitoramento em tempo real
    7. Coletar dados de expressão (simulado ou real)
    8. Calcular métricas de alinhamento e reprodutibilidade
    9. Ancorar resultados na TemporalChain
    """

    def __init__(
        self,
        config: ExperimentalConfig,
        temporal_chain=None,
        meta_audit=None,
    ):
        self.config = config
        self.temporal = temporal_chain
        self.meta_audit = meta_audit

        # Inicializar componentes
        self.rnaseq_engine = RNASeqCalibrationEngine(config.rnaseq_data_dir)

        hardware_config = HardwareConfig(
            hardware_type=OptogeneticHardware[config.hardware_type.upper()],
            wavelength_nm=config.wavelength_nm,
            max_power_mw_mm2=config.max_power_mw_mm2,
            spatial_resolution_um=10.0,
            temporal_resolution_ms=10.0,
            field_of_view_mm=(1.0, 1.0),
            z_stack_support=True,
        )
        self.opto_adapter = OptogeneticsPlatformAdapter(
            config=hardware_config,
            safety_monitor=self._safety_monitor_callback,
        )

        self._results: List[ExperimentalResult] = []

    async def run_experiment(
        self,
        field_3d: Optional[np.ndarray] = None,  # Campo vetorial do P2I
        replicate: int = 1,
    ) -> ExperimentalResult:
        """
        Executa experimento neurogenético completo.

        Args:
            field_3d: Campo vetorial 3D do P2I (opcional, gera mock se None)
            replicate: Número da réplica experimental

        Returns:
            ExperimentalResult com todos os resultados
        """
        experiment_id = hashlib.sha3_256(
            f"{self.config.semantic_term}:{replicate}:{time.time()}".encode()
        ).hexdigest()[:12]

        logger.info(f"🧪 Iniciando experimento: {experiment_id} | '{self.config.semantic_term}' | réplica {replicate}")

        # 1. Calibrar perfil gênico com RNA-Seq
        logger.info("📊 Calibrando perfil gênico com dados RNA-Seq...")
        calibrated_profile = self.rnaseq_engine.calibrate_semantic_gene_map(
            self.config.semantic_term
        )
        calibration_confidence = self._compute_calibration_confidence(calibrated_profile)

        # 2. Construir GRN não-linear
        logger.info("🧠 Construindo GRN não-linear...")
        grn_interactions = self._build_grn_for_semantic_term(
            self.config.semantic_term, self.config.grn_interactions
        )
        grn_simulator = NonlinearGRNSimulator(
            interactions=grn_interactions,
            initial_state=self._create_initial_grn_state(calibrated_profile),
        )

        # 3. Simular dinâmica gênica com sinal externo do P2I
        logger.info("⚡ Simulando dinâmica gênica com sinal P2I...")

        def external_signal_fn(time_minutes: float, gene: str) -> float:
            """Gera sinal externo baseado no campo vetorial (mock se field_3d=None)."""
            if field_3d is None:
                # Mock: sinal oscilatório para demonstração
                return 0.3 + 0.2 * np.sin(time_minutes * 0.1)
            else:
                # Em produção: interpolar campo na posição/tempo
                return np.mean(np.linalg.norm(field_3d, axis=-1)) * 0.5

        grn_final_state = await grn_simulator.simulate(
            external_signal_fn=external_signal_fn,
            callback=lambda t, s: logger.debug(f"  t={t:.0f}min: CREB={s.protein_level.get('CREB1', 0):.3f}")
        )
        grn_summary = grn_simulator.get_state_summary(grn_final_state)

        # 4. Conectar e aplicar padrão no hardware optogenético
        logger.info("💡 Aplicando padrão no hardware optogenético...")
        connected = await self.opto_adapter.connect()

        if connected and field_3d is not None:
            # Converter campo para padrão de luz
            applied = await self.opto_adapter.apply_field_as_light(
                field_3d=field_3d,
                duration_ms=1000,
                safety_check=True,
            )
        else:
            applied = False
            logger.warning("⚠️  Padrão não aplicado (hardware desconectado ou field_3d=None)")

        safety_violations = len([
            e for e in self.opto_adapter.get_exposure_log()
            if e.get("max_intensity", 0) > self.config.safety_limits.get("max_irradiance_mw_mm2", 10)
        ])

        # 5. Calcular métricas de sucesso
        # Alinhamento: quão próximo o estado final está do perfil alvo
        alignment_score = self._compute_alignment_score(
            grn_final_state.protein_level, calibrated_profile
        )

        # Reprodutibilidade: mock para demo (em produção: comparar réplicas)
        reproducibility_score = 0.85 + np.random.normal(0, 0.05)

        # 6. Construir resultado
        result = ExperimentalResult(
            experiment_id=experiment_id,
            semantic_term=self.config.semantic_term,
            config_hash=hashlib.sha3_256(
                json.dumps(self.config.__dict__, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            calibrated_profile=calibrated_profile,
            calibration_confidence=calibration_confidence,
            grn_final_state={k: float(v) for k, v in grn_final_state.protein_level.items()},
            grn_convergence_time=grn_summary.get("last_update_time", 0),
            light_pattern_applied=applied,
            safety_violations=safety_violations,
            alignment_score=float(np.clip(alignment_score, 0, 1)),
            reproducibility_score=float(np.clip(reproducibility_score, 0, 1)),
        )

        # 7. Ancorar na TemporalChain
        if self.temporal:
            result.temporal_seal = await self.temporal.anchor_event(
                "neurogenetic_experiment_completed",
                {
                    "experiment_id": experiment_id,
                    "semantic_term": self.config.semantic_term,
                    "alignment_score": result.alignment_score,
                    "calibration_confidence": calibration_confidence,
                    "genes_targeted": len(calibrated_profile),
                    "replicate": replicate,
                    "timestamp": result.timestamp,
                }
            )

        # 8. Registrar no MetaAudit
        if self.meta_audit:
            await self.meta_audit.record_cycle(
                prompt=self.config.semantic_term,
                vlm_score=result.alignment_score,
                best_individual=result,
                population_size=1,
                generations=1,
                environment_id=f"neurogenetic_experimental_{self.config.hardware_type}",
                phi_c=result.alignment_score,
                additional_metadata={
                    "calibration_confidence": calibration_confidence,
                    "grn_genes": len(grn_final_state.protein_level),
                    "safety_violations": safety_violations,
                }
            )

        self._results.append(result)

        logger.info(
            f"✅ Experimento concluído: {experiment_id} | "
            f"alignment={result.alignment_score:.3f} | "
            f"reprod={result.reproducibility_score:.3f} | "
            f"selo={result.temporal_seal[:16] if result.temporal_seal else 'N/A'}"
        )

        return result

    def _compute_calibration_confidence(self, profile: Dict[str, float]) -> float:
        """Calcula confiança da calibração baseada em qualidade dos dados."""
        if not profile:
            return 0.0

        # Fatores de confiança:
        # • Número de genes calibrados
        # • Significância estatística média
        # • Consistência entre estudos
        gene_count_score = min(1.0, len(profile) / 20)  # 20 genes = score máximo

        # Mock para significância (em produção: calcular dos dados RNA-Seq)
        significance_score = 0.9

        # Consistência (mock)
        consistency_score = 0.85

        return (gene_count_score * 0.4 + significance_score * 0.4 + consistency_score * 0.2)

    def _build_grn_for_semantic_term(
        self,
        semantic_term: str,
        base_interactions: List[GRNInteraction],
    ) -> List[GRNInteraction]:
        """Constrói GRN específica para termo semântico."""
        # Começar com interações base
        interactions = base_interactions.copy()

        # Adicionar interações específicas por termo
        if "memory" in semantic_term.lower():
            # Reforçar loop CREB→BDNF→CREB para plasticidade
            interactions.append(
                GRNInteraction("BDNF", "CREB1", InteractionType.FEEDBACK_POSITIVE, 0.15)
            )
        elif "neurogen" in semantic_term.lower():
            # Adicionar via ASCL1→NEUROD1→DCX para neurogênese
            interactions.extend([
                GRNInteraction("external_signal", "ASCL1", InteractionType.ACTIVATION, 0.9, hill_coefficient=2.0),
                GRNInteraction("ASCL1", "NEUROD1", InteractionType.ACTIVATION, 0.8),
                GRNInteraction("NEUROD1", "DCX", InteractionType.ACTIVATION, 0.75),
            ])
        elif "anxiety" in semantic_term.lower():
            # Reforçar via RELN→GAD para modulação inibitória
            interactions.append(
                GRNInteraction("RELN", "GAD1", InteractionType.ACTIVATION, 0.6)
            )

        return interactions

    def _create_initial_grn_state(self, target_profile: Dict[str, float]) -> GRNState:
        """Cria estado inicial da GRN baseado no perfil alvo."""
        # Estado basal: expressão baixa para todos os genes
        initial_expr = {gene: 0.1 for gene in target_profile.keys()}
        initial_protein = {gene: 0.05 for gene in target_profile.keys()}

        return GRNState(
            gene_expression=initial_expr,
            protein_level=initial_protein,
        )

    def _compute_alignment_score(
        self,
        actual_state: Dict[str, float],
        target_profile: Dict[str, float],
    ) -> float:
        """Calcula score de alinhamento entre estado real e perfil alvo."""
        if not target_profile:
            return 0.5

        scores = []
        for gene, target in target_profile.items():
            actual = actual_state.get(gene, 0.0)
            # Similaridade com penalidade por overshoot
            error = abs(actual - target)
            scores.append(1.0 - error)

        return np.mean(scores) if scores else 0.5

    async def _safety_monitor_callback(self, params: Dict) -> bool:
        """Callback para monitoramento de segurança em tempo real."""
        # Verificar limites adicionais
        if params.get("max_intensity", 0) > self.config.safety_limits.get("max_irradiance_mw_mm2", 10):
            logger.warning("⚠️  Intensidade excede limite de segurança")
            return False
        return True

    def get_results_summary(self) -> Dict:
        """Retorna resumo consolidado de todos os experimentos."""
        if not self._results:
            return {"experiments": 0}

        alignment_scores = [r.alignment_score for r in self._results]
        reproducibility_scores = [r.reproducibility_score for r in self._results]

        return {
            "total_experiments": len(self._results),
            "by_semantic_term": {
                term: {
                    "count": sum(1 for r in self._results if r.semantic_term == term),
                    "avg_alignment": np.mean([r.alignment_score for r in self._results if r.semantic_term == term]),
                }
                for term in set(r.semantic_term for r in self._results)
            },
            "overall_metrics": {
                "avg_alignment": np.mean(alignment_scores),
                "std_alignment": np.std(alignment_scores),
                "avg_reproducibility": np.mean(reproducibility_scores),
                "calibration_confidence_avg": np.mean([r.calibration_confidence for r in self._results]),
            },
            "safety": {
                "total_violations": sum(r.safety_violations for r in self._results),
                "hardware_success_rate": sum(1 for r in self._results if r.light_pattern_applied) / len(self._results),
            },
        }
