#!/usr/bin/env python3
"""
Substrato 198‑C: WetlabAdapter — Simulação Biofísica
Traduz campos vetoriais 3D em atuadores simulados (gradientes químicos,
campos elétricos) para testar o loop ZapGPT em modelos de partículas
com comportamento coletivo (xenobots simulados).
"""

import asyncio
import numpy as np
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActuatorType(Enum):
    """Tipos de atuadores suportados."""
    CHEMICAL_GRADIENT = "chemical_gradient"   # Gradiente de morfógeno
    ELECTRIC_FIELD = "electric_field"         # Campo elétrico
    LIGHT_PATTERN = "light_pattern"           # Padrão de luz (optogenética)
    MECHANICAL_FORCE = "mechanical_force"     # Força mecânica direta

@dataclass
class BioParticle:
    """Representa uma partícula biológica simulada (célula, xenobot)."""
    position: np.ndarray          # [x, y, z]
    velocity: np.ndarray          # [vx, vy, vz]
    cell_type: str = "stem"       # "stem", "muscle", "neuron"
    age: float = 0.0              # Idade da célula em segundos
    energy: float = 1.0           # Energia metabólica (0‑1)
    adhesion: float = 0.5         # Força de adesão celular
    sensitivity: Dict[ActuatorType, float] = field(default_factory=lambda: {
        ActuatorType.CHEMICAL_GRADIENT: 0.8,
        ActuatorType.ELECTRIC_FIELD: 0.6,
        ActuatorType.LIGHT_PATTERN: 0.4,
        ActuatorType.MECHANICAL_FORCE: 1.0
    })

@dataclass
class BioEnvironment:
    """Ambiente biofísico simulado."""
    particles: List[BioParticle]
    world_size: float = 1.0       # mm (escala microscópica)
    temperature: float = 37.0     # °C
    viscosity: float = 0.001      # Pa·s (água)
    time_step: float = 0.1        # segundos
    chemical_field: Optional[np.ndarray] = None   # Concentração de morfógeno
    electric_field: Optional[np.ndarray] = None   # Campo elétrico

    def apply_actuators(self, actuators: Dict[ActuatorType, np.ndarray]) -> None:
        """
        Aplica múltiplos atuadores sobre as partículas.

        Args:
            actuators: Dicionário mapeando tipo de atuador → campo 3D
        """
        for particle in self.particles:
            total_force = np.zeros(3)

            for actuator_type, field in actuators.items():
                if actuator_type not in particle.sensitivity:
                    continue

                sensitivity = particle.sensitivity[actuator_type]

                # Interpolar campo na posição da partícula
                force = self._interpolate_field(field, particle.position)

                # Escalar pela sensibilidade da célula
                total_force += force * sensitivity

            # Aplicar força (com viscosidade)
            acceleration = total_force / (6 * np.pi * self.viscosity * 0.01)  # Lei de Stokes
            particle.velocity += acceleration * self.time_step
            particle.position += particle.velocity * self.time_step

            # Consumo de energia
            particle.energy -= 0.001 * np.linalg.norm(total_force)
            particle.energy = np.clip(particle.energy, 0.0, 1.0)

            # Envelhecimento
            particle.age += self.time_step

    def _interpolate_field(self, field: np.ndarray, position: np.ndarray) -> np.ndarray:
        """Interpolação trilinear do campo na posição da partícula."""
        W, H, D, _ = field.shape

        # Normalizar posição para coordenadas do campo
        x = position[0] / self.world_size * (W - 1)
        y = position[1] / self.world_size * (H - 1)
        z = position[2] / self.world_size * (D - 1)

        # Índices dos cantos
        x0, x1 = int(np.floor(x)), min(int(np.ceil(x)), W - 1)
        y0, y1 = int(np.floor(y)), min(int(np.ceil(y)), H - 1)
        z0, z1 = int(np.floor(z)), min(int(np.ceil(z)), D - 1)

        # Pesos de interpolação
        wx1, wx0 = x - x0, x1 - x
        wy1, wy0 = y - y0, y1 - y
        wz1, wz0 = z - z0, z1 - z

        # Interpolação trilinear
        value = (
            wx0 * wy0 * wz0 * field[x0, y0, z0] +
            wx1 * wy0 * wz0 * field[x1, y0, z0] +
            wx0 * wy1 * wz0 * field[x0, y1, z0] +
            wx0 * wy0 * wz1 * field[x0, y0, z1] +
            wx1 * wy1 * wz0 * field[x1, y1, z0] +
            wx1 * wy0 * wz1 * field[x1, y0, z1] +
            wx0 * wy1 * wz1 * field[x0, y1, z1] +
            wx1 * wy1 * wz1 * field[x1, y1, z1]
        ) / 1.0

        return value

    def step_cell_division(self) -> None:
        """Simula divisão celular simples."""
        new_particles = []
        for particle in self.particles:
            if particle.energy > 0.8 and particle.age > 3600:  # 1 hora
                # Criar célula filha
                daughter = BioParticle(
                    position=particle.position + np.random.randn(3) * 0.01,
                    velocity=np.random.randn(3) * 0.01,
                    cell_type=particle.cell_type,
                    energy=0.4,
                    adhesion=particle.adhesion,
                    sensitivity=particle.sensitivity.copy()
                )
                new_particles.append(daughter)
                particle.energy -= 0.4

        self.particles.extend(new_particles)

class WetlabBioSimAdapter:
    """
    Adaptador para simulação biofísica.

    Traduz campos vetoriais 3D do P2I em atuadores biológicos simulados.
    Permite testar o loop ZapGPT em modelos de partículas com comportamento
    coletivo antes de migrar para hardware biológico real.
    """

    def __init__(
        self,
        actuator_mapping: Dict[str, ActuatorType] = None,
        meta_audit: Optional[callable] = None,
        temporal_chain=None
    ):
        self.actuator_mapping = actuator_mapping or {
            "chemical": ActuatorType.CHEMICAL_GRADIENT,
            "electric": ActuatorType.ELECTRIC_FIELD,
            "light": ActuatorType.LIGHT_PATTERN,
            "force": ActuatorType.MECHANICAL_FORCE
        }
        self.meta_audit = meta_audit
        self.temporal = temporal_chain
        self._history: List[Dict] = []

    async def translate_field_to_actuators(
        self,
        field_3d: np.ndarray,          # Campo vetorial do P2I [W, H, D, 3]
        actuator_type: str = "chemical"
    ) -> Dict[ActuatorType, np.ndarray]:
        """
        Traduz campo vetorial 3D em atuadores biológicos.

        Para gradiente químico:
        - Magnitude do campo → concentração de morfógeno
        - Direção do campo → gradiente direcional

        Para campo elétrico:
        - Campo é usado diretamente como força elétrica
        """
        actuator = self.actuator_mapping.get(actuator_type)
        if actuator is None:
            raise ValueError(f"Tipo de atuador desconhecido: {actuator_type}")

        if actuator == ActuatorType.CHEMICAL_GRADIENT:
            # Magnitude do campo → concentração
            magnitude = np.linalg.norm(field_3d, axis=-1)
            # Normalizar para concentração (0‑1)
            concentration = magnitude / (np.max(magnitude) + 1e-8)
            # Expandir para 3 canais (gradiente em cada direção)
            chemical_field = field_3d.copy()
            chemical_field[..., 0] *= concentration
            chemical_field[..., 1] *= concentration
            chemical_field[..., 2] *= concentration
            return {actuator: chemical_field}

        elif actuator == ActuatorType.ELECTRIC_FIELD:
            # Usar campo diretamente como campo elétrico
            return {actuator: field_3d}

        elif actuator == ActuatorType.MECHANICAL_FORCE:
            # Força mecânica direta
            return {actuator: field_3d}

        else:  # LIGHT_PATTERN
            # Intensidade luminosa baseada na magnitude
            intensity = np.linalg.norm(field_3d, axis=-1)
            light_field = np.stack([intensity] * 3, axis=-1)
            return {actuator: light_field}

    async def run_biosim_loop(
        self,
        prompt: str,
        generations: int = 20,
        population_size: int = 10,
        num_particles: int = 50,
        duration_steps: int = 1000
    ) -> Dict:
        """
        Executa loop completo com simulação biofísica.

        Pipeline:
        1. Prompt → P2I → campo vetorial 3D
        2. Campo → atuadores biológicos
        3. Atuadores → BioEnvironment → evolução temporal
        4. Estado final → imagem → VLM (simulado)
        5. Evolução do P2I via μ+λ ES
        """
        logger.info(f"🧪 BioSim Loop: '{prompt}' com {num_particles} partículas")

        # Criar ambiente biológico
        particles = []
        for _ in range(num_particles):
            pos = np.random.rand(3) * 1.0  # mm
            vel = np.random.randn(3) * 0.001
            particles.append(BioParticle(position=pos, velocity=vel))

        env = BioEnvironment(particles=particles)

        # Campo inicial (MVP: gerado deterministicamente)
        resolution = (8, 8, 8)
        field = np.random.randn(*resolution, 3) * 0.01  # Ruído como ponto de partida

        # Evolução simplificada
        best_score = 0.0
        best_field = field.copy()

        for gen in range(generations):
            # Gerar população com mutações
            population = [best_field + np.random.randn(*resolution, 3) * 0.01]

            for candidate in population:
                # Traduzir campo para atuadores
                actuators = await self.translate_field_to_actuators(candidate, "chemical")

                # Criar ambiente fresco para cada avaliação
                fresh_particles = []
                for _ in range(num_particles):
                    pos = np.random.rand(3) * 1.0
                    vel = np.random.randn(3) * 0.001
                    fresh_particles.append(BioParticle(position=pos, velocity=vel))

                test_env = BioEnvironment(particles=fresh_particles)

                # Executar simulação
                for _ in range(duration_steps):
                    test_env.apply_actuators(actuators)

                # Avaliar resultado (score heurístico)
                positions = np.array([p.position for p in test_env.particles])
                center = np.mean(positions, axis=0)

                if "cluster" in prompt.lower():
                    distances = np.linalg.norm(positions - center, axis=1)
                    score = 1.0 - np.mean(distances) / 0.5
                elif "torus" in prompt.lower():
                    radii = np.linalg.norm(positions[:, :2] - center[:2], axis=1)
                    target = 0.3
                    error = np.abs(radii - target)
                    score = 1.0 - np.mean(error) / 0.3
                else:
                    score = 0.5

                score = np.clip(score, 0.0, 1.0)

                if score > best_score:
                    best_score = score
                    best_field = candidate.copy()
                    logger.info(f"   Gen {gen+1}: novo melhor score = {best_score:.3f}")

        result = {
            "prompt": prompt,
            "best_score": best_score,
            "num_particles": num_particles,
            "duration_steps": duration_steps,
            "field_hash": hashlib.sha3_256(best_field.tobytes()).hexdigest()[:16],
            "timestamp": time.time()
        }

        # Ancorar via MetaAudit
        if self.meta_audit:
            result["temporal_seal"] = await self.meta_audit(
                prompt=prompt,
                vlm_score=best_score,
                best_individual=best_field,
                population_size=population_size,
                generations=generations,
                environment_id="biosim_chemical_gradient"
            )

        self._history.append(result)
        return result
