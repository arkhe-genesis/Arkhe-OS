#!/usr/bin/env python3
"""
Substrato 198-E: Integração NeurogeneticFieldInterface + WetlabBioSimAdapterV2
Canon: ∞.Ω.∇+++.198.E.integration
Função: Unifica o loop P2I-VLM com dinâmica de GRN e atuadores biofísicos
Pipeline completo: prompt → embedding → campo 3D → atuadores → GRN dynamics → score
Integração: 198-E (NeurogeneticFieldInterface), 198-C v2 (WetlabBioSimAdapterV2), 9018 (TemporalChain)
"""
import asyncio
import numpy as np
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar componentes existentes
# from neurogenetic_field_interface import NeurogeneticFieldInterface, NeuralCircuit, GeneTarget
# from wetlab.biosim_adapter_v2 import WetlabBioSimAdapterV2, BioEnvironmentV2, BioParticleV2
# from meta_audit_sidecar import MetaAuditSidecar

@dataclass
class UnifiedNeurogeneticConfig:
    """Configuração unificada para pipeline neurogenético integrado."""
    # Configurações do campo 3D
    field_resolution: Tuple[int, int, int] = (8, 8, 8)
    world_size_mm: float = 1.0  # Escala microscópica em mm

    # Configurações biofísicas
    num_particles: int = 50
    particle_radius_um: float = 10.0  # 10 μm típico para células
    viscosity_pa_s: float = 0.001  # Água a 37°C
    temperature_k: float = 310.15  # 37°C

    # Configurações da GRN
    grn_update_dt_hours: float = 0.1  # Passo de atualização da GRN
    grn_propagation_steps: int = 3  # Passos de propagação por ciclo

    # Configurações de atuadores
    actuator_type: str = "chemical_gradient"  # chemical, electric, light, force
    actuator_efficiency: float = 0.8  # Eficiência de transdução campo→atuador

    # Configurações evolutivas
    evolution_generations: int = 30
    population_size: int = 10
    mutation_sigma: float = 0.1

    # Configurações de score
    spatial_weight: float = 0.4  # Peso da métrica espacial
    grn_weight: float = 0.4  # Peso da métrica de expressão gênica
    temporal_weight: float = 0.2  # Peso da métrica temporal/dinâmica


@dataclass
class UnifiedExecutionResult:
    """Resultado de uma execução do pipeline unificado."""
    execution_id: str
    prompt: str
    prompt_hash: str

    # Resultados do campo 3D
    field_hash: str
    optimal_intensity: float
    optimal_pulse_ms: float

    # Resultados da GRN
    final_grn_state: Dict[str, float]
    grn_score: float

    # Resultados espaciais
    final_positions: np.ndarray
    spatial_score: float

    # Score composto
    composite_score: float

    # Metadados
    generations: int
    population_size: int
    config_hash: str
    timestamp: float

    # Ancoragem
    temporal_seal: Optional[str] = None


class UnifiedNeurogeneticPipeline:
    """
    Pipeline unificado que integra:
    1. NeurogeneticFieldInterface (prompt → perfil gênico → score GRN)
    2. WetlabBioSimAdapterV2 (campo 3D → atuadores → dinâmica biofísica)
    3. MetaAuditSidecar (registro imutável de cada ciclo)

    Fluxo completo:
    prompt → embedding SBERT → perfil gênico alvo + campo vetorial 3D
           → atuadores biofísicos (chemical/electric/light/force)
           → BioEnvironmentV2 com GRN dynamics
           → score composto (espacial + GRN + temporal)
           → evolução μ+λ ES sobre parâmetros ópticos
           → ancoragem na TemporalChain
    """

    def __init__(
        self,
        config: UnifiedNeurogeneticConfig,
        meta_audit: Optional[Any] = None,
        temporal_chain: Optional[Any] = None,
        phi_bus: Optional[Any] = None,
    ):
        self.config = config
        self.meta_audit = meta_audit
        self.temporal = temporal_chain
        self.phi_bus = phi_bus

        self._history: List[UnifiedExecutionResult] = []
        self._results_dir = Path("/tmp/neurogenetic_unified")
        self._results_dir.mkdir(exist_ok=True)

    async def execute_pipeline(
        self,
        prompt: str,
        initial_grn_state: Optional[Dict[str, float]] = None,
    ) -> UnifiedExecutionResult:
        """
        Executa o pipeline unificado completo.

        Args:
            prompt: Instrução em linguagem natural
                   (ex: "consolidate memory", "induce neurogenesis")
            initial_grn_state: Estado inicial opcional da GRN
                              (usa padrão se None)

        Returns:
            UnifiedExecutionResult com todos os resultados
        """
        execution_id = hashlib.sha3_256(
            f"{prompt}:{time.time()}".encode()
        ).hexdigest()[:12]

        prompt_hash = hashlib.sha3_256(prompt.encode()).hexdigest()[:16]

        logger.info(f"🧬 Pipeline unificado: '{prompt}' (exec_id: {execution_id})")

        # 1. Converter prompt para perfil gênico alvo + embedding
        target_gene_profile = self._prompt_to_refined_gene_profile(prompt)
        embedding = self._prompt_to_embedding(prompt)

        # 2. Gerar campo vetorial 3D inicial a partir do embedding
        initial_field = self._embedding_to_3d_field(embedding)

        # 3. Evolução μ+λ ES para otimizar parâmetros ópticos
        best_result = await self._evolve_optical_params(
            prompt=prompt,
            target_profile=target_gene_profile,
            initial_field=initial_field,
            initial_grn_state=initial_grn_state,
        )

        # 4. Construir resultado
        result = UnifiedExecutionResult(
            execution_id=execution_id,
            prompt=prompt,
            prompt_hash=prompt_hash,
            field_hash=best_result["field_hash"],
            optimal_intensity=best_result["optimal_intensity"],
            optimal_pulse_ms=best_result["optimal_pulse_ms"],
            final_grn_state=best_result["final_grn_state"],
            grn_score=best_result["grn_score"],
            final_positions=best_result["final_positions"],
            spatial_score=best_result["spatial_score"],
            composite_score=best_result["composite_score"],
            generations=self.config.evolution_generations,
            population_size=self.config.population_size,
            config_hash=hashlib.sha3_256(
                json.dumps(self.config.__dict__, sort_keys=True, default=str).encode()
            ).hexdigest()[:16],
            timestamp=time.time(),
        )

        # 5. Ancorar na TemporalChain
        if self.temporal:
            result.temporal_seal = await self._anchor_execution(result)

        # 6. Registrar no MetaAudit
        if self.meta_audit:
            await self.meta_audit.record_cycle(
                prompt=prompt,
                vlm_score=result.composite_score,
                best_individual=result,
                population_size=self.config.population_size,
                generations=self.config.evolution_generations,
                environment_id="neurogenetic_unified_v2",
                phi_c=result.composite_score,
                additional_metadata={
                    "grn_score": result.grn_score,
                    "spatial_score": result.spatial_score,
                    "target_profile": {k: v for k, v in target_gene_profile.items()},
                }
            )

        self._history.append(result)

        logger.info(
            f"✅ Pipeline concluído: score={result.composite_score:.4f} | "
            f"GRN={result.grn_score:.4f} | Espacial={result.spatial_score:.4f}"
        )

        return result

    def _prompt_to_refined_gene_profile(self, prompt: str) -> Dict[str, float]:
        """
        Converte prompt em perfil gênico alvo usando SEMANTIC_GENE_MAP refinado.

        Baseado em literatura de neurociência experimental:
        • CREB: hub central de plasticidade sináptica (Silva et al., 1998)
        • FOS/EGR1: immediate early genes para ativação neuronal (Herdegen & Leah, 1998)
        • BDNF: neurotrofina para sobrevivência e diferenciação (Huang & Reichardt, 2001)
        • ARC: regulação de endocitose de receptores AMPA (Chowdhury et al., 2006)
        • ASCL1/DCX: marcadores de neurogênese adulta (Zhao et al., 2008)
        """
        prompt_lower = prompt.lower()

        # Mapeamento refinado baseado em literatura experimental
        REFINED_SEMANTIC_GENE_MAP = {
            # === Memória e Plasticidade Sináptica ===
            "consolidate memory": {
                "CREB": 0.95,    # Hub de plasticidade (Silva et al., 1998)
                "FOS": 0.85,     # IEG para ativação neuronal
                "EGR1": 0.80,    # IEG para consolidação
                "BDNF": 0.75,    # Suporte trófico para LTP
                "ARC": 0.70,     # Regulação de AMPA para estabilização
            },
            "recall memory": {
                "FOS": 0.90,     # Reativação de engramas
                "ARC": 0.85,     # Reciclagem de receptores
                "EGR1": 0.75,
                "CREB": 0.60,    # Menor que consolidação
            },
            "enhance plasticity": {
                "CREB": 0.90,
                "BDNF": 0.85,    # Principal regulador de plasticidade
                "FOS": 0.70,
                "RELN": 0.60,    # Modulação de LTP via reelin
            },

            # === Neurogênese e Diferenciação ===
            "induce neurogenesis": {
                "ASCL1": 0.95,   # Fator pró-neurogênico mestre
                "DCX": 0.90,     # Marcador de neuroblastos
                "BDNF": 0.80,    # Suporte de sobrevivência
                "CREB": 0.60,    # Modulação indireta
            },
            "promote differentiation": {
                "DCX": 0.90,
                "NEUROD1": 0.85, # Fator de diferenciação neuronal
                "BDNF": 0.70,
                "SOX2": 0.30,    # Downregulation de pluripotência
            },
            "maintain pluripotency": {
                "SOX2": 0.95,
                "OCT4": 0.90,
                "NANOG": 0.85,
                "ASCL1": 0.10,   # Supressão de diferenciação
            },

            # === Resposta ao Estresse e Inflamação ===
            "silence anxiety": {
                "RELN": 0.80,    # Modulação de circuitos de medo
                "BDNF": 0.70,    # Efeito ansiolítico indireto
                "FOS": 0.40,     # Redução de ativação neuronal
                "NR4A1": 0.50,   # Regulação de resposta ao estresse
            },
            "suppress inflammation": {
                "BDNF": 0.75,    # Efeito anti-inflamatório
                "RELN": 0.60,
                "FOS": 0.30,     # Redução de ativação microglial
            },
            "respond to injury": {
                "FOS": 0.90,     # Resposta imediata a dano
                "EGR1": 0.85,
                "BDNF": 0.80,    # Reparo e neuroproteção
                "ARC": 0.60,
            },

            # === Padrões Espaciais e Coletivos ===
            "form a cluster": {
                "FOS": 0.75,     # Ativação coordenada
                "EGR1": 0.65,
                "CREB": 0.55,
                "BDNF": 0.50,    # Adesão mediada por BDNF
            },
            "synchronize activity": {
                "CREB": 0.85,    # Sincronização via plasticidade
                "BDNF": 0.80,
                "FOS": 0.70,
            },
            "migrate toward target": {
                "DCX": 0.85,     # Migração de neuroblastos
                "BDNF": 0.75,    # Quimioatração via BDNF
                "FOS": 0.60,
            },

            # === Padrões de Inibição ===
            "scatter apart": {
                "FOS": 0.40,     # Baixa ativação coordenada
                "RELN": 0.60,    # Modulação de adesão
            },
            "reduce activity": {
                "FOS": 0.30,
                "EGR1": 0.30,
                "CREB": 0.40,
            },
        }

        # Matching semântico com fallback
        for key, profile in REFINED_SEMANTIC_GENE_MAP.items():
            if key in prompt_lower:
                return profile.copy()

        # Fallback: perfil balanceado baseado em contexto
        if any(term in prompt_lower for term in ["memory", "plasticity", "learn"]):
            return {"CREB": 0.7, "FOS": 0.6, "EGR1": 0.5, "BDNF": 0.5}
        elif any(term in prompt_lower for term in ["neurogen", "differentiat", "stem"]):
            return {"ASCL1": 0.7, "DCX": 0.6, "BDNF": 0.5}
        elif any(term in prompt_lower for term in ["anxiet", "stress", "inflamm"]):
            return {"RELN": 0.6, "BDNF": 0.5, "FOS": 0.4}
        else:
            # Perfil neutro
            return {"FOS": 0.5, "EGR1": 0.4, "CREB": 0.3}

    def _prompt_to_embedding(self, prompt: str) -> np.ndarray:
        """Converte prompt em embedding (mock SBERT — em produção, usar sentence-transformers)."""
        seed = int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        return rng.normal(0, 1, 384)

    def _embedding_to_3d_field(self, embedding: np.ndarray) -> np.ndarray:
        """Projeta embedding em campo vetorial 3D."""
        resolution = self.config.field_resolution
        rng = np.random.RandomState(int(embedding[0] * 1000) % (2**32))

        # Campo base com ruído estruturado
        field = rng.normal(0, 0.3, (*resolution, 3))

        # Modulação pelo embedding (simplificado)
        modulation = np.tanh(embedding[:3])
        for i in range(3):
            field[..., i] *= modulation[i]

        return field

    async def _evolve_optical_params(
        self,
        prompt: str,
        target_profile: Dict[str, float],
        initial_field: np.ndarray,
        initial_grn_state: Optional[Dict[str, float]],
    ) -> Dict:
        """Evolução μ+λ ES para otimizar parâmetros ópticos."""
        best_score = -1.0
        best_params = {"intensity": 0.5, "pulse_ms": 1000.0}
        best_field = initial_field.copy()

        # Inicializar população
        population = []
        for _ in range(self.config.population_size):
            intensity = np.clip(np.random.normal(0.5, 0.2), 0.0, 1.0)
            pulse_ms = np.clip(np.random.normal(1000, 300), 100, 5000)
            field_noise = np.random.normal(0, self.config.mutation_sigma, initial_field.shape)
            population.append({
                "intensity": intensity,
                "pulse_ms": pulse_ms,
                "field": initial_field + field_noise,
            })

        for gen in range(self.config.evolution_generations):
            # Avaliar população
            results = []
            for individual in population:
                res = await self._evaluate_individual(
                    prompt=prompt,
                    target_profile=target_profile,
                    params=individual,
                    initial_grn_state=initial_grn_state,
                )
                results.append(res)

            # Selecionar melhores
            scores = [r["composite_score"] for r in results]
            best_idx = int(np.argmax(scores))
            if scores[best_idx] > best_score:
                best_score = scores[best_idx]
                best_params = {
                    "intensity": population[best_idx]["intensity"],
                    "pulse_ms": population[best_idx]["pulse_ms"],
                }
                best_field = population[best_idx]["field"].copy()

            # Gerar nova população (elitismo + mutação)
            new_population = [population[best_idx].copy()]  # Elitismo
            for _ in range(self.config.population_size - 1):
                parent = population[np.random.choice(
                    np.argsort(scores)[-3:],  # Top 3
                    p=np.array([0.5, 0.3, 0.2])
                )]
                child = {
                    "intensity": np.clip(
                        parent["intensity"] + np.random.normal(0, 0.1), 0.0, 1.0
                    ),
                    "pulse_ms": np.clip(
                        parent["pulse_ms"] + np.random.normal(0, 100), 100, 5000
                    ),
                    "field": parent["field"] + np.random.normal(
                        0, self.config.mutation_sigma, initial_field.shape
                    ),
                }
                new_population.append(child)

            population = new_population

            if gen % 5 == 0:
                logger.info(f"  Gen {gen}: best_score={best_score:.4f}")

        # Avaliação final com mais passos de simulação
        final_result = await self._evaluate_individual(
            prompt=prompt,
            target_profile=target_profile,
            params={**best_params, "field": best_field},
            initial_grn_state=initial_grn_state,
            extended_simulation=True,
        )

        return {
            **final_result,
            "optimal_intensity": best_params["intensity"],
            "optimal_pulse_ms": best_params["pulse_ms"],
            "field_hash": hashlib.sha3_256(best_field.tobytes()).hexdigest()[:16],
        }

    async def _evaluate_individual(
        self,
        prompt: str,
        target_profile: Dict[str, float],
        params: Dict,
        initial_grn_state: Optional[Dict[str, float]],
        extended_simulation: bool = False,
    ) -> Dict:
        """Avalia um indivíduo da população."""
        # 1. Traduzir campo para atuadores
        from wetlab.biosim_adapter_v2 import WetlabBioSimAdapterV2, ActuatorType

        adapter = WetlabBioSimAdapterV2(
            actuator_mapping={"chemical": ActuatorType.CHEMICAL_GRADIENT}
        )
        actuators = await adapter.translate_field_to_actuators(
            params["field"],
            actuator_type=self.config.actuator_type,
        )

        # 2. Executar simulação biofísica com GRN
        from wetlab.biosim_adapter_v2 import BioEnvironmentV2, BioParticleV2

        particles = []
        for i in range(self.config.num_particles):
            pos = np.random.rand(3) * self.config.world_size_mm
            vel = np.random.randn(3) * 0.001
            particle = BioParticleV2(position=pos, velocity=vel)

            # Inicializar GRN se estado inicial fornecido
            if initial_grn_state:
                for gene, level in initial_grn_state.items():
                    if gene in particle.grn.genes:
                        particle.grn.genes[gene] = level

            particles.append(particle)

        env = BioEnvironmentV2(
            particles=particles,
            world_size=self.config.world_size_mm,
            viscosity=self.config.viscosity_pa_s,
            temperature=self.config.temperature_k,
            time_step=0.1,
        )

        # Parâmetros de simulação
        duration_steps = 2000 if extended_simulation else 500

        # Executar simulação
        for step in range(duration_steps):
            # Aplicar atuadores com parâmetros ópticos
            scaled_actuators = {}
            for act_type, field_data in actuators.items():
                # Escalar por intensidade e padrão de pulso
                pulse_factor = min(1.0, params["pulse_ms"] / 1000)
                scaled_actuators[act_type] = field_data * params["intensity"] * pulse_factor

            env.apply_actuators_with_grn(scaled_actuators)

            # Propagar GRN
            if step % 10 == 0:  # Atualizar GRN a cada 10 passos físicos
                for particle in env.particles:
                    if isinstance(particle, BioParticleV2):
                        particle.update_grn(
                            dt=self.config.grn_update_dt_hours,
                            field_signal=np.zeros(3)  # Simplificado
                        )

        # 3. Calcular scores
        positions = np.array([p.position for p in env.particles])

        # Score espacial
        spatial_score = self._compute_spatial_score(prompt, positions)

        # Score GRN
        grn_summary = env.get_grn_summary()
        grn_score = self._compute_grn_score(target_profile, grn_summary)

        # Score temporal (simplificado: estabilidade ao longo do tempo)
        temporal_score = 0.8  # Placeholder

        # Score composto
        composite_score = (
            spatial_score * self.config.spatial_weight +
            grn_score * self.config.grn_weight +
            temporal_score * self.config.temporal_weight
        )

        return {
            "final_grn_state": grn_summary,
            "grn_score": grn_score,
            "final_positions": positions,
            "spatial_score": spatial_score,
            "composite_score": np.clip(composite_score, 0.0, 1.0),
        }

    def _compute_spatial_score(self, prompt: str, positions: np.ndarray) -> float:
        """Calcula score baseado em métrica espacial."""
        if len(positions) < 2:
            return 0.5

        prompt_lower = prompt.lower()

        if any(term in prompt_lower for term in ["cluster", "group", "gather"]):
            # Clustering: distância par a par baixa
            diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
            dists = np.sqrt(np.sum(diff**2, axis=2))
            mask = np.triu(np.ones_like(dists), k=1).astype(bool)
            avg_dist = np.mean(dists[mask])
            return max(0.0, min(1.0, 1.0 - avg_dist / (self.config.world_size_mm * 0.5)))

        elif any(term in prompt_lower for term in ["scatter", "dispers", "apart"]):
            # Dispersão: distância par a par alta
            diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
            dists = np.sqrt(np.sum(diff**2, axis=2))
            mask = np.triu(np.ones_like(dists), k=1).astype(bool)
            avg_dist = np.mean(dists[mask])
            return max(0.0, min(1.0, avg_dist / (self.config.world_size_mm * 0.5)))

        else:
            # Padrão neutro
            return 0.5

    def _compute_grn_score(self, target: Dict[str, float], actual: Dict[str, float]) -> float:
        """Calcula score de alinhamento entre perfil gênico alvo e estado atual."""
        if not target:
            return 0.5

        scores = []
        for gene, target_level in target.items():
            actual_level = actual.get(gene, 0.0)
            # Similaridade com penalidade por overshoot
            error = abs(actual_level - target_level)
            scores.append(1.0 - error)

        return float(np.mean(scores)) if scores else 0.5

    async def _anchor_execution(self, result: UnifiedExecutionResult) -> str:
        """Ancora resultado na TemporalChain."""
        seal = await self.temporal.anchor_event(
            "unified_neurogenetic_execution",
            {
                "execution_id": result.execution_id,
                "prompt_hash": result.prompt_hash,
                "composite_score": result.composite_score,
                "grn_score": result.grn_score,
                "spatial_score": result.spatial_score,
                "field_hash": result.field_hash,
                "config_hash": result.config_hash,
                "timestamp": result.timestamp,
            }
        )
        logger.info(f"🔐 Execução ancorada: selo {seal[:16]}")
        return seal

    def get_history(self) -> List[UnifiedExecutionResult]:
        """Retorna histórico de execuções."""
        return self._history.copy()
