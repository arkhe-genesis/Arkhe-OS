#!/usr/bin/env python3
"""
ARKHE OS Substrato 198‑C v3: BioSim com Arquitetura de Cristae Mitocondriais
Canon: ∞.Ω.∇+++.198.C.v3
Função: Simulação biofísica com gradientes de prótons, ATP sintase simulada,
         e dinâmica de fusão/fissão — inspirado por Rao et al. (2026).
Integração: 198‑B (MetaAudit), 198‑E (Neurogenetic), 9018 (TemporalChain)

Isomorfismo com o Tear (181):
    • Gradiente de prótons → Compulsão Bruta (força motriz)
    • ATP sintase (rotação) → Paridade (bifurcação do sinal em ação)
    • Feedback [ATP]/[ADP] → Espelho (realimentação fecha o loop)
"""

import asyncio
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES BIOFÍSICAS DAS CRISTAE
# ═══════════════════════════════════════════════════════════════════════════════

# Potencial de membrana mitocondrial típico (mV)
DELTA_PSI_RESTING = -150.0       # mV (interior negativo)
DELTA_PSI_DEPOLARIZED = -50.0    # mV (limiar de disfunção)
PROTON_GRADIENT_FORCE = 0.02     # Força motriz próton-motriz por mV
ATP_SYNTHASE_RATE = 100.0        # moléculas ATP/s por complexo
CARDIOLIPIN_AFINITY = 0.8        # afinidade da cardiolipina por prótons
FUSION_THRESHOLD = 0.3           # limiar energético para fusão
FISSION_THRESHOLD = 0.7          # limiar energético para fissão
MEMBRANE_PERMEABILITY = 0.05     # vazamento de prótons por unidade de tempo


class CristaeState(Enum):
    """Estados funcionais da crista mitocondrial."""
    HEALTHY = "healthy"           # ΔΨ alto, ATP produção normal
    COMPENSATING = "compensating" # ΔΨ moderado, tentando restaurar
    DEPOLARIZED = "depolarized"   # ΔΨ baixo, disfunção
    FUSING = "fusing"             # Em processo de fusão
    FISSIONING = "fissioning"     # Em processo de fissão


@dataclass
class ProtonGradient:
    """
    Gradiente eletroquímico de prótons através da membrana interna.

    Análogo à Compulsão Bruta (181): a força motriz que impulsiona todo o sistema.
    """
    delta_psi: float = DELTA_PSI_RESTING      # potencial de membrana (mV)
    matrix_protons: float = 0.7                # [H+] na matriz (0‑1 normalizado)
    intermembrane_protons: float = 0.3         # [H+] no espaço intermembrana
    cardiolipin_bound: float = 0.2             # prótons ligados à cardiolipina
    leak_rate: float = MEMBRANE_PERMEABILITY   # taxa de vazamento

    def proton_motive_force(self) -> float:
        """Calcula a força próton‑motriz combinada (Δp)."""
        # Δp = ΔΨ - (RT/F) * ΔpH (simplificado)
        delta_ph = -np.log10(
            self.intermembrane_protons / max(self.matrix_protons, 1e-6)
        )
        # Normalizado para 0‑1
        force = abs(self.delta_psi) / abs(DELTA_PSI_RESTING) * 0.7 + abs(delta_ph) * 0.3
        return float(np.clip(force, 0.0, 1.0))

    def update(self, dt: float, atp_synthase_activity: float, external_field: float):
        """
        Atualiza o gradiente baseado na atividade da ATP sintase e campo externo.

        Args:
            dt: intervalo de tempo
            atp_synthase_activity: fração de ATP sintases ativas (0‑1)
            external_field: intensidade do campo externo (0‑1) — análogo ao P2I
        """
        # Produção de gradiente pela cadeia respiratória (influenciada pelo campo)
        proton_pumping = external_field * PROTON_GRADIENT_FORCE * dt * 100

        # Consumo pela ATP sintase
        proton_consumption = atp_synthase_activity * ATP_SYNTHASE_RATE * dt / 1000

        # Vazamento passivo
        proton_leak = self.leak_rate * (self.intermembrane_protons - self.matrix_protons) * dt

        # Atualizar concentrações
        self.intermembrane_protons += proton_pumping - proton_consumption - proton_leak
        self.matrix_protons += proton_consumption - proton_pumping * 0.3 + proton_leak

        # Cardioplipina tampona prótons
        cardiolipin_binding = CARDIOLIPIN_AFINITY * (
            self.intermembrane_protons - self.cardiolipin_bound
        ) * dt
        self.cardiolipin_bound += cardiolipin_binding
        self.intermembrane_protons -= cardiolipin_binding * 0.1

        # Clamp
        self.intermembrane_protons = float(np.clip(self.intermembrane_protons, 0.05, 0.95))
        self.matrix_protons = float(np.clip(self.matrix_protons, 0.05, 0.95))
        self.cardiolipin_bound = float(np.clip(self.cardiolipin_bound, 0.0, 0.5))

        # Atualizar potencial de membrana
        ratio = self.intermembrane_protons / max(self.matrix_protons, 1e-6)
        self.delta_psi = DELTA_PSI_RESTING * float(np.clip(ratio, 0.3, 1.0))


@dataclass
class ATPsynthase:
    """
    ATP sintase simulada — o motor rotativo que converte gradiente em energia.

    Análogo à Paridade (181): converte a força motriz (gradiente) em ação (ATP).
    """
    activity: float = 0.5                     # fração de complexos ativos (0‑1)
    rotation_speed_rps: float = 100.0         # rotações por segundo
    atp_produced: float = 0.0                 # ATP acumulado (unidades arbitrárias)
    efficiency: float = 0.65                  # eficiência termodinâmica

    def update(self, dt: float, proton_force: float):
        """
        Atualiza a produção de ATP baseado na força próton‑motriz.

        Args:
            dt: intervalo de tempo
            proton_force: força próton‑motriz normalizada (0‑1)
        """
        # Rotação impulsionada pelo fluxo de prótons
        self.rotation_speed_rps = ATP_SYNTHASE_RATE * proton_force * self.activity

        # Produção de ATP (~3 prótons por ATP)
        atp_synthesis = self.rotation_speed_rps * dt / 3.0 * self.efficiency

        # Consumo metabólico basal
        basal_consumption = 0.01 * dt

        self.atp_produced += atp_synthesis - basal_consumption
        self.atp_produced = max(0.0, self.atp_produced)


@dataclass
class CristaeParticle:
    """
    Partícula que carrega uma crista mitocondrial simulada.

    Herda propriedades de BioParticleV2 (posição, velocidade, GRN)
    e adiciona gradiente de prótons, ATP sintase e estado da crista.
    """
    # Propriedades físicas (herdadas de BioParticle)
    id: int = 0
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    mass: float = 1.0
    radius: float = 0.1
    age: float = 0.0
    energy: float = 1.0
    adhesion: float = 0.5

    # Crista mitocondrial
    gradient: ProtonGradient = field(default_factory=ProtonGradient)
    atp_synthase: ATPsynthase = field(default_factory=ATPsynthase)
    cristae_state: CristaeState = CristaeState.HEALTHY

    # Estado genético (herdado de BioParticleV2)
    grn: Optional[Any] = None
    differentiation_state: str = "pluripotent"
    sensitivity: Dict[str, float] = field(default_factory=lambda: {
        "chemical_gradient": 0.8,
        "electric_field": 0.6,
        "light_pattern": 0.9,
        "mechanical_force": 1.0,
        "crispr_activation": 0.95,
    })

    def apply_force(self, force: np.ndarray, dt: float):
        """Aplica força segundo F = ma."""
        acceleration = force / self.mass
        self.velocity += acceleration * dt
        self.position += self.velocity * dt

    def update_cristae(self, dt: float, external_field: float):
        """
        Atualiza o estado da crista baseado no campo externo (análogo ao P2I).

        O campo externo é a "Compulsão Bruta" (181) que impulsiona o gradiente.
        """
        # Atualizar gradiente
        self.gradient.update(dt, self.atp_synthase.activity, external_field)

        # Atualizar ATP sintase
        proton_force = self.gradient.proton_motive_force()
        self.atp_synthase.update(dt, proton_force)

        # Atualizar estado da crista
        self._update_cristae_state()

        # Consumo de energia proporcional à atividade
        self.energy -= self.atp_synthase.activity * 0.001 * dt
        self.energy = float(np.clip(self.energy, 0.0, 1.0))

        # Envelhecimento
        self.age += dt

    def _update_cristae_state(self):
        """Determina o estado funcional da crista."""
        if self.gradient.delta_psi < DELTA_PSI_DEPOLARIZED:
            self.cristae_state = CristaeState.DEPOLARIZED
        elif self.gradient.delta_psi > DELTA_PSI_RESTING * 0.8:
            self.cristae_state = CristaeState.HEALTHY
        else:
            self.cristae_state = CristaeState.COMPENSATING

    def can_fuse(self) -> bool:
        """Verifica se a partícula pode se fundir com outra."""
        return self.energy < FUSION_THRESHOLD and self.cristae_state != CristaeState.FUSING

    def can_fission(self) -> bool:
        """Verifica se a partícula pode fissionar."""
        return (self.energy > FISSION_THRESHOLD and
                self.atp_synthase.atp_produced > 10.0 and
                self.cristae_state != CristaeState.FISSIONING)

    def fuse_with(self, other: 'CristaeParticle') -> 'CristaeParticle':
        """Funde duas partículas em uma maior."""
        if not self.can_fuse() or not other.can_fuse():
            return None

        # Nova posição: média ponderada
        new_pos = (self.position * self.mass + other.position * other.mass) / (
            self.mass + other.mass
        )

        # Novo gradiente: combinação dos dois
        new_gradient = ProtonGradient(
            delta_psi=(self.gradient.delta_psi + other.gradient.delta_psi) / 2,
            matrix_protons=(self.gradient.matrix_protons + other.gradient.matrix_protons) / 2,
            intermembrane_protons=(
                self.gradient.intermembrane_protons + other.gradient.intermembrane_protons
            ) / 2,
            cardiolipin_bound=(
                self.gradient.cardiolipin_bound + other.gradient.cardiolipin_bound
            ) / 2,
        )

        # Nova ATP sintase: soma das atividades
        new_atp_synthase = ATPsynthase(
            activity=min(1.0, self.atp_synthase.activity + other.atp_synthase.activity),
            atp_produced=self.atp_synthase.atp_produced + other.atp_synthase.atp_produced,
        )

        # Criar partícula filha
        daughter = CristaeParticle(
            position=new_pos,
            mass=self.mass + other.mass,
            radius=(self.radius**3 + other.radius**3)**(1/3),
            energy=min(1.0, self.energy + other.energy),
            gradient=new_gradient,
            atp_synthase=new_atp_synthase,
            cristae_state=CristaeState.FUSING,
            age=max(self.age, other.age),
            adhesion=max(self.adhesion, other.adhesion),
        )

        # Desativar partículas originais
        self.energy = 0.0
        other.energy = 0.0

        return daughter

    def fission(self) -> List['CristaeParticle']:
        """Divide a partícula em duas menores."""
        if not self.can_fission():
            return []

        # Cada filha recebe metade da energia e ATP
        half_energy = self.energy / 2
        half_atp = self.atp_synthase.atp_produced / 2

        # Gradientes ligeiramente diferentes para criar diversidade
        daughter1 = CristaeParticle(
            position=self.position + np.random.randn(3) * 0.02,
            mass=self.mass / 2,
            radius=self.radius * 0.7,
            energy=half_energy,
            gradient=ProtonGradient(
                delta_psi=self.gradient.delta_psi * 1.1,
                matrix_protons=self.gradient.matrix_protons * 1.05,
                intermembrane_protons=self.gradient.intermembrane_protons * 0.95,
            ),
            atp_synthase=ATPsynthase(activity=self.atp_synthase.activity * 0.6, atp_produced=half_atp),
            cristae_state=CristaeState.FISSIONING,
            age=self.age,
            adhesion=self.adhesion * 0.8,
        )

        daughter2 = CristaeParticle(
            position=self.position + np.random.randn(3) * 0.02,
            mass=self.mass / 2,
            radius=self.radius * 0.7,
            energy=half_energy,
            gradient=ProtonGradient(
                delta_psi=self.gradient.delta_psi * 0.9,
                matrix_protons=self.gradient.matrix_protons * 0.95,
                intermembrane_protons=self.gradient.intermembrane_protons * 1.05,
            ),
            atp_synthase=ATPsynthase(activity=self.atp_synthase.activity * 0.4, atp_produced=half_atp),
            cristae_state=CristaeState.FISSIONING,
            age=self.age,
            adhesion=self.adhesion * 0.8,
        )

        # Desativar partícula original
        self.energy = 0.0

        return [daughter1, daughter2]

    def get_matrix_protons(self) -> float:
        """Retorna a concentração de prótons na matriz."""
        return self.gradient.matrix_protons


@dataclass
class CristaeEnvironment:
    """
    Ambiente que simula um conjunto de cristae mitocondriais.

    Análogo ao tecido de coerência (185): múltiplas cristae interagindo
    via campo externo (P2I) e forças locais (repulsão, adesão).
    """
    particles: List[CristaeParticle] = field(default_factory=list)
    world_size: float = 10.0
    time_step: float = 0.01
    step_count: int = 0

    def _init_particles(self, num: int):
        """Inicializa partículas com cristae aleatórias."""
        rng = np.random.RandomState(42)
        for i in range(num):
            pos = rng.uniform(-self.world_size/2, self.world_size/2, 3)
            # Variar o gradiente inicial
            delta_psi = DELTA_PSI_RESTING * rng.uniform(0.7, 1.0)
            gradient = ProtonGradient(delta_psi=float(delta_psi))
            atp_synthase = ATPsynthase(activity=float(rng.uniform(0.3, 0.9)))

            self.particles.append(CristaeParticle(
                id=i,
                position=pos,
                gradient=gradient,
                atp_synthase=atp_synthase,
                energy=float(rng.uniform(0.5, 0.9)),
            ))

    def step(self, external_field: np.ndarray = None):
        """
        Avança a simulação em um passo.

        Args:
            external_field: campo vetorial 3D do P2I (opcional)
        """
        dt = self.time_step

        for particle in self.particles:
            if particle.energy <= 0.0:
                continue

            # Calcular intensidade do campo externo na posição da partícula
            field_intensity = 0.5  # default
            if external_field is not None:
                field_intensity = self._sample_field(external_field, particle.position)

            # Atualizar crista (gradiente + ATP sintase)
            particle.update_cristae(dt, field_intensity)

            # Força de repulsão local (evitar sobreposição)
            repulsion = np.zeros(3)
            for other in self.particles:
                if other.id != particle.id and other.energy > 0.0:
                    diff = particle.position - other.position
                    dist = np.linalg.norm(diff)
                    if dist < 2 * particle.radius and dist > 1e-6:
                        repulsion += diff / dist * (2 * particle.radius - dist) * 5.0

            # Força de adesão (proporcional à cardiolipina)
            adhesion_force = particle.adhesion * particle.gradient.cardiolipin_bound * 0.1

            # Força total
            total_force = repulsion * (1.0 - adhesion_force) + np.random.randn(3) * 0.01

            # Aplicar
            particle.apply_force(total_force, dt)

            # Boundary conditions
            half = self.world_size / 2
            for dim in range(3):
                if particle.position[dim] < -half:
                    particle.position[dim] = -half
                    particle.velocity[dim] *= -0.5
                elif particle.position[dim] > half:
                    particle.position[dim] = half
                    particle.velocity[dim] *= -0.5

        # Dinâmica de fusão/fissão
        self._process_fusion_fission()

        self.step_count += 1

    def _sample_field(self, field: np.ndarray, position: np.ndarray) -> float:
        """Amostra o campo externo na posição da partícula."""
        if field is None:
            return 0.5

        W, H, D = field.shape[:3]
        x = (position[0] / (self.world_size/2) * (W/2) + W/2)
        y = (position[1] / (self.world_size/2) * (H/2) + H/2)
        z = (position[2] / (self.world_size/2) * (D/2) + D/2)

        x0, x1 = int(np.clip(x, 0, W-2)), int(np.clip(x, 0, W-2)) + 1
        y0, y1 = int(np.clip(y, 0, H-2)), int(np.clip(y, 0, H-2)) + 1
        z0, z1 = int(np.clip(z, 0, D-2)), int(np.clip(z, 0, D-2)) + 1

        wx, wy, wz = x - x0, y - y0, z - z0

        value = (
            field[x0,y0,z0] * (1-wx)*(1-wy)*(1-wz) +
            field[x1,y0,z0] * wx*(1-wy)*(1-wz) +
            field[x0,y1,z0] * (1-wx)*wy*(1-wz) +
            field[x0,y0,z1] * (1-wx)*(1-wy)*wz +
            field[x1,y1,z0] * wx*wy*(1-wz) +
            field[x1,y0,z1] * wx*(1-wy)*wz +
            field[x0,y1,z1] * (1-wx)*wy*wz +
            field[x1,y1,z1] * wx*wy*wz
        ) / 1.0

        return float(np.mean(value))

    def _process_fusion_fission(self):
        """Processa eventos de fusão e fissão entre partículas."""
        new_particles = []
        to_remove = set()

        # Verificar fusão (partículas próximas com baixa energia)
        for i, p1 in enumerate(self.particles):
            if i in to_remove or p1.energy <= 0.0 or not p1.can_fuse():
                continue
            for j, p2 in enumerate(self.particles):
                if j <= i or j in to_remove or p2.energy <= 0.0 or not p2.can_fuse():
                    continue
                dist = np.linalg.norm(p1.position - p2.position)
                if dist < p1.radius + p2.radius:
                    daughter = p1.fuse_with(p2)
                    if daughter:
                        new_particles.append(daughter)
                        to_remove.add(i)
                        to_remove.add(j)
                        break

        # Verificar fissão (partículas com alta energia)
        for i, p in enumerate(self.particles):
            if i in to_remove or p.energy <= 0.0 or not p.can_fission():
                continue
            daughters = p.fission()
            if daughters:
                new_particles.extend(daughters)
                to_remove.add(i)

        # Atualizar lista de partículas
        self.particles = [p for i, p in enumerate(self.particles) if i not in to_remove]
        self.particles.extend(new_particles)

        # Re-indexar
        for i, p in enumerate(self.particles):
            p.id = i

    def get_cristae_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do estado das cristae."""
        active = [p for p in self.particles if p.energy > 0.0]
        if not active:
            return {}

        states = {}
        for state in CristaeState:
            count = sum(1 for p in active if p.cristae_state == state)
            states[state.value] = count

        return {
            "total_particles": len(self.particles),
            "active_particles": len(active),
            "avg_delta_psi": float(np.mean([p.gradient.delta_psi for p in active])),
            "avg_atp": float(np.mean([p.atp_synthase.atp_produced for p in active])),
            "avg_proton_force": float(np.mean([p.gradient.proton_motive_force() for p in active])),
            "state_distribution": states,
            "cardiolipin_total": float(np.sum([p.gradient.cardiolipin_bound for p in active])),
        }


class CristaeBioSim:
    """
    Simulador biofísico inspirado na arquitetura das cristae mitocondriais.

    Integra o loop P2I (campo externo) com a dinâmica interna de cada crista,
    permitindo que prompts linguísticos modulem a bioenergética celular simulada.

    Isomorfismo com o Tear (181):
        • Campo P2I → Compulsão Bruta (força motriz externa)
        • Gradiente de prótons → Paridade (bifurcação em componentes)
        • ATP sintase → Espelho (feedback fecha o loop)
    """

    def __init__(
        self,
        num_particles: int = 50,
        world_size: float = 10.0,
        meta_audit: Optional[Any] = None,
        temporal_chain: Optional[Any] = None
    ):
        self.env = CristaeEnvironment(world_size=world_size)
        self.env._init_particles(num_particles)
        self.meta_audit = meta_audit
        self.temporal = temporal_chain
        self._history: List[Dict] = []

    def _prompt_to_field(self, prompt: str, resolution: tuple = (8, 8, 8)) -> np.ndarray:
        """Converte prompt em campo de luz 3D (análogo ao P2I)."""
        seed = int(hashlib.sha3_256(prompt.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        field = rng.uniform(0.3, 0.9, resolution)
        return field

    async def run(
        self,
        prompt: str,
        generations: int = 30,
        population_size: int = 10,
        duration_steps: int = 500
    ) -> Dict:
        """
        Executa o loop completo com arquitetura de cristae.

        Pipeline:
        1. Prompt → campo vetorial 3D (P2I)
        2. Campo aplicado como força externa sobre cada crista
        3. Cristae atualizam gradiente, produzem ATP
        4. Fusão/fissão baseada em estado energético
        5. Score combinado: coerência do gradiente + produção de ATP
        6. Evolução do campo via μ+λ ES
        """
        logger.info(f"🔬 CristaeBioSim: '{prompt}' ({generations} gerações)")
        prompt_hash = hashlib.sha3_256(prompt.encode()).hexdigest()[:16]
        resolution = (8, 8, 8)

        # Campo inicial
        best_field = self._prompt_to_field(prompt, resolution)
        best_score = -1.0

        for gen in range(generations):
            # Mutação do campo
            mutation = np.random.normal(0, 0.05, best_field.shape)
            candidate = np.clip(best_field + mutation, 0.0, 1.0)

            # Criar ambiente fresco
            env = CristaeEnvironment(world_size=self.env.world_size)
            env._init_particles(50)

            # Executar simulação
            for _ in range(duration_steps):
                env.step(candidate)

            # Calcular score: coerência do gradiente + produção de ATP
            stats = env.get_cristae_stats()
            delta_psi_score = abs(stats.get("avg_delta_psi", 0)) / abs(DELTA_PSI_RESTING)
            atp_score = min(1.0, stats.get("avg_atp", 0) / 50.0)
            score = delta_psi_score * 0.5 + atp_score * 0.5

            if score > best_score:
                best_score = score
                best_field = candidate.copy()

            if gen % 10 == 0:
                logger.info(f"  Gen {gen}: score={score:.3f} (ΔΨ={delta_psi_score:.3f}, ATP={atp_score:.3f})")

        # Simulação final com melhor campo
        env = CristaeEnvironment(world_size=self.env.world_size)
        env._init_particles(50)
        for _ in range(duration_steps * 2):
            env.step(best_field)

        final_stats = env.get_cristae_stats()

        result = {
            "prompt": prompt,
            "prompt_hash": prompt_hash,
            "best_score": best_score,
            "final_stats": final_stats,
            "field_hash": hashlib.sha3_256(best_field.tobytes()).hexdigest()[:16],
            "generations": generations,
            "duration_steps": duration_steps,
            "timestamp": time.time(),
            "isomorphism": {
                "gradient": "Compulsão Bruta (181)",
                "atp_synthase": "Paridade (181)",
                "feedback": "Espelho (181)",
                "cardiolipin": "Token Arkhe (176)"
            }
        }

        if self.meta_audit:
            if asyncio.iscoroutinefunction(self.meta_audit):
                result["temporal_seal"] = await self.meta_audit(
                    prompt=prompt,
                    vlm_score=best_score,
                    best_individual=best_field,
                    population_size=population_size,
                    generations=generations,
                    environment_id="cristae_biosim_v3"
                )
            else:
                result["temporal_seal"] = self.meta_audit(
                    prompt=prompt,
                    vlm_score=best_score,
                    best_individual=best_field,
                    population_size=population_size,
                    generations=generations,
                    environment_id="cristae_biosim_v3"
                )

        self._history.append(result)
        logger.info(f"✅ CristaeBioSim: score={best_score:.3f}, ΔΨ={final_stats.get('avg_delta_psi',0):.1f}mV")

        return result


# ═══════════════════════════════════════════════════════════════
# TESTES UNITÁRIOS
# ═══════════════════════════════════════════════════════════════

async def test_cristae_biosim():
    """Testa o BioSim com arquitetura de cristae."""
    print("\n" + "="*70)
    print("TESTE: Cristae BioSim — Substrato 198‑C v3")
    print("="*70)

    # Teste 1: Gradiente de prótons
    print("\n[Teste 1] Gradiente de prótons")
    grad = ProtonGradient()
    assert abs(grad.delta_psi - DELTA_PSI_RESTING) < 1.0
    force = grad.proton_motive_force()
    print(f"  Força próton‑motriz inicial: {force:.3f}")
    assert 0.5 < force < 1.0

    # Teste 2: ATP sintase
    print("\n[Teste 2] ATP sintase")
    atp = ATPsynthase()
    atp.update(1.0, 0.8)
    print(f"  ATP produzido: {atp.atp_produced:.1f}")
    assert atp.atp_produced > 0

    # Teste 3: Crista completa
    print("\n[Teste 3] Crista completa")
    particle = CristaeParticle()
    particle.update_cristae(1.0, 0.6)
    print(f"  ΔΨ: {particle.gradient.delta_psi:.1f} mV")
    print(f"  ATP: {particle.atp_synthase.atp_produced:.1f}")
    print(f"  Estado: {particle.cristae_state.value}")
    assert particle.atp_synthase.atp_produced > 0

    # Teste 4: Fusão
    print("\n[Teste 4] Fusão de cristae")
    p1 = CristaeParticle(position=np.array([0.0, 0.0, 0.0]), energy=0.2)
    p2 = CristaeParticle(position=np.array([0.15, 0.0, 0.0]), energy=0.2)
    daughter = p1.fuse_with(p2)
    if daughter:
        print(f"  Fusão bem‑sucedida: massa={daughter.mass:.2f}, energia={daughter.energy:.2f}")
        assert daughter.mass == 2.0
    else:
        print("  Fusão não ocorreu (thresholds não atingidos)")

    # Teste 5: Loop completo
    print("\n[Teste 5] Loop completo")
    biosim = CristaeBioSim(num_particles=20)
    result = await biosim.run(
        prompt="maintain proton gradient",
        generations=5,
        population_size=4,
        duration_steps=100
    )
    print(f"  Score: {result['best_score']:.3f}")
    print(f"  ΔΨ médio: {result['final_stats']['avg_delta_psi']:.1f} mV")
    print(f"  ATP médio: {result['final_stats']['avg_atp']:.1f}")
    print(f"  Isomorfismo: {result['isomorphism']}")
    assert result['best_score'] > 0.0

    print("\n✅ TODOS OS TESTES PASSARAM")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_cristae_biosim())