#!/usr/bin/env python3
"""
Substrato 198‑A: ZapGPT‑3D MVP
Motor 3D simplificado com PyBullet para validar generalização do loop
P2I‑VLM para três dimensões. Testa prompts canônicos: "cluster", "torus", "grid".
"""

import asyncio
import numpy as np
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

# Em produção: import pybullet as p
# Para MVP: simular ambiente 3D com arrays numpy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Body3D:
    """Representa um corpo no ambiente 3D."""
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    radius: float = 0.1
    mass: float = 1.0

@dataclass
class Environment3D:
    """Ambiente 3D simplificado."""
    bodies: List[Body3D]
    world_size: float = 10.0
    gravity: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, -9.81]))
    time_step: float = 0.01

    def apply_field(self, field: np.ndarray) -> None:
        """
        Aplica campo vetorial 3D sobre os corpos.

        Args:
            field: Tensor [W, H, D, 3] com vetores de força
        """
        W, H, D, _ = field.shape

        for body in self.bodies:
            # Normalizar posição para índices do campo
            x_idx = int(np.clip(body.position[0] / self.world_size * W, 0, W - 1))
            y_idx = int(np.clip(body.position[1] / self.world_size * H, 0, H - 1))
            z_idx = int(np.clip(body.position[2] / self.world_size * D, 0, D - 1))

            # Obter força do campo na posição do corpo
            force = field[x_idx, y_idx, z_idx]

            # Aplicar força + gravidade
            acceleration = force / body.mass + self.gravity
            body.velocity += acceleration * self.time_step
            body.position += body.velocity * self.time_step

            # Condições de contorno (paredes refletoras)
            body.position = np.clip(body.position, 0, self.world_size)
            if body.position[0] <= 0 or body.position[0] >= self.world_size:
                body.velocity[0] *= -0.5
            if body.position[1] <= 0 or body.position[1] >= self.world_size:
                body.velocity[1] *= -0.5
            if body.position[2] <= 0 or body.position[2] >= self.world_size:
                body.velocity[2] *= -0.5

    def step(self, num_steps: int = 1):
        """Avança a simulação por num_steps passos (sem campo externo)."""
        for _ in range(num_steps):
            for body in self.bodies:
                body.velocity += self.gravity * self.time_step
                body.position += body.velocity * self.time_step
                body.position = np.clip(body.position, 0, self.world_size)

class ZapGPT3D_MVP:
    """
    MVP do ZapGPT‑3D.

    Simplificações em relação ao 2D:
    • Campo vetorial 3D gerado por convoluções transpostas
    • Ambiente 3D com 100 corpos e física newtoniana
    • VLM simulado (score baseado em heurística)
    • Evolução (μ+λ ES) com população de 10, 30 gerações
    """

    CANONICAL_PROMPTS = ["cluster", "torus", "grid"]

    def __init__(self, meta_audit: Optional[callable] = None):
        self.meta_audit = meta_audit
        self._history: List[Dict] = []

    async def generate_field(self, prompt: str, resolution: Tuple[int, int, int] = (5, 5, 5)) -> np.ndarray:
        """
        Simula P2I: prompt → embedding → campo vetorial 3D.

        Para MVP, gera campo determinístico baseado no hash do prompt.
        Em produção: SentenceTransformer → convoluções transpostas.
        """
        # Seed determinística baseada no prompt
        seed = int(hashlib.sha3_256(prompt.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)

        # Gerar campo vetorial 3D
        W, H, D = resolution
        field = np.zeros((W, H, D, 3))

        if "cluster" in prompt.lower():
            # Campo que aponta para o centro
            center = np.array([W/2, H/2, D/2])
            for x in range(W):
                for y in range(H):
                    for z in range(D):
                        pos = np.array([x, y, z])
                        direction = center - pos
                        norm = np.linalg.norm(direction)
                        if norm > 0:
                            field[x, y, z] = direction / norm * 0.5

        elif "torus" in prompt.lower():
            # Campo que forma um torus (anel 3D)
            center = np.array([W/2, H/2, D/2])
            major_radius = min(W, H) / 3
            for x in range(W):
                for y in range(H):
                    for z in range(D):
                        pos = np.array([x, y, z])
                        # Distância ao anel principal
                        dist_to_ring = abs(np.sqrt((pos[0]-center[0])**2 + (pos[1]-center[1])**2) - major_radius)
                        # Força radial para manter no anel
                        radial_dir = pos[:2] - center[:2]
                        if np.linalg.norm(radial_dir) > 0:
                            radial_dir = radial_dir / np.linalg.norm(radial_dir)
                        field[x, y, z, :2] = -radial_dir * dist_to_ring * 0.1
                        # Força vertical para planarizar
                        field[x, y, z, 2] = (center[2] - z) * 0.05

        elif "grid" in prompt.lower():
            # Campo que alinha em grid 3D
            grid_spacing = 2.0
            for x in range(W):
                for y in range(H):
                    for z in range(D):
                        # Posição alvo no grid mais próximo
                        grid_x = round(x / grid_spacing) * grid_spacing
                        grid_y = round(y / grid_spacing) * grid_spacing
                        grid_z = round(z / grid_spacing) * grid_spacing
                        target = np.array([grid_x, grid_y, grid_z])
                        direction = target - np.array([x, y, z])
                        norm = np.linalg.norm(direction)
                        if norm > 0:
                            field[x, y, z] = direction / norm * 0.3

        return field

    async def evaluate_result(self, prompt: str, field: np.ndarray, num_steps: int = 500) -> float:
        """
        Simula VLM‑D2R: executa simulação e retorna score de alinhamento.

        Para MVP, calcula score heurístico baseado na distribuição final.
        Em produção: Mistral‑Vision ou modelo local avaliaria imagem renderizada.
        """
        # Criar ambiente com corpos aleatórios
        num_bodies = 50
        bodies = []
        for _ in range(num_bodies):
            pos = np.random.rand(3) * 10.0
            vel = np.random.randn(3) * 0.1
            bodies.append(Body3D(position=pos, velocity=vel))

        env = Environment3D(bodies=bodies)

        # Executar simulação
        for step in range(num_steps):
            env.apply_field(field)

        # Calcular score heurístico baseado no prompt
        positions = np.array([b.position for b in env.bodies])

        if "cluster" in prompt.lower():
            # Score: quão próximos estão os corpos do centro
            center = np.mean(positions, axis=0)
            distances = np.linalg.norm(positions - center, axis=1)
            score = 1.0 - np.mean(distances) / 5.0  # Normalizado
        elif "torus" in prompt.lower():
            # Score: quão bem formam um anel
            center = np.mean(positions, axis=0)
            radii = np.linalg.norm(positions[:, :2] - center[:2], axis=1)
            target_radius = 3.0
            radius_error = np.abs(radii - target_radius)
            score = 1.0 - np.mean(radius_error) / 3.0
        elif "grid" in prompt.lower():
            # Score: quão bem alinhados em grid
            # Quantizar posições para grid
            grid_spacing = 2.0
            quantized = np.round(positions / grid_spacing) * grid_spacing
            alignment_error = np.linalg.norm(positions - quantized, axis=1)
            score = 1.0 - np.mean(alignment_error) / grid_spacing
        else:
            score = 0.5  # Neutro

        return np.clip(score, 0.0, 1.0)

    async def run_loop(
        self,
        prompt: str,
        population_size: int = 10,
        generations: int = 30,
        resolution: Tuple[int, int, int] = (5, 5, 5)
    ) -> Dict:
        """
        Executa loop completo P2I → Simulação → VLM → Evolução para 3D.

        Returns:
            Dict com resultados do melhor indivíduo e métricas
        """
        logger.info(f"🚀 ZapGPT‑3D MVP: processando '{prompt}' ({generations} gerações)")

        # Evolução (μ+λ ES simplificada)
        best_field = await self.generate_field(prompt, resolution)
        best_score = await self.evaluate_result(prompt, best_field)

        sigma = 0.1  # Taxa de mutação

        for gen in range(generations):
            # Gerar população (campo base + ruído gaussiano)
            population = []
            for _ in range(population_size):
                mutation = np.random.normal(0, sigma, best_field.shape)
                candidate = best_field + mutation
                candidate = np.clip(candidate, -1.0, 1.0)  # Limitar forças
                population.append(candidate)

            # Avaliar população
            scores = []
            for candidate in population:
                score = await self.evaluate_result(prompt, candidate, num_steps=200)  # Avaliação rápida
                scores.append(score)

            # Selecionar melhor
            best_idx = np.argmax(scores)
            if scores[best_idx] > best_score:
                best_score = scores[best_idx]
                best_field = population[best_idx]
                logger.info(f"   Gen {gen+1}: novo melhor score = {best_score:.3f}")

            # Ajustar sigma adaptativamente
            if gen % 10 == 0 and gen > 0:
                sigma *= 0.9  # Decaimento da mutação

        # Avaliação final completa (mais passos de simulação)
        final_score = await self.evaluate_result(prompt, best_field, num_steps=1000)

        result = {
            "prompt": prompt,
            "final_score": final_score,
            "best_score_evolution": best_score,
            "field_resolution": resolution,
            "generations": generations,
            "population_size": population_size,
            "field_hash": hashlib.sha3_256(best_field.tobytes()).hexdigest()[:16],
            "timestamp": time.time()
        }

        # Ancorar via MetaAudit
        if self.meta_audit:
            result["temporal_seal"] = await self.meta_audit(
                prompt=prompt,
                vlm_score=final_score,
                best_individual=best_field,
                population_size=population_size,
                generations=generations,
                environment_id="zapgpt_3d_mvp"
            )

        self._history.append(result)
        return result

    async def validate_canonical_prompts(self) -> Dict:
        """Executa validação com prompts canônicos: cluster, torus, grid."""
        results = {}
        for prompt in self.CANONICAL_PROMPTS:
            logger.info(f"\n{'='*60}\n🔬 Validando prompt canônico: '{prompt}'\n{'='*60}")
            result = await self.run_loop(prompt)
            results[prompt] = result
            logger.info(f"✅ '{prompt}' → score final = {result['final_score']:.3f}\n")

        # Sumário
        success_count = sum(1 for r in results.values() if r["final_score"] >= 0.5)
        return {
            "results": results,
            "success_count": success_count,
            "total_prompts": len(self.CANONICAL_PROMPTS),
            "success_rate": success_count / len(self.CANONICAL_PROMPTS),
            "avg_score": np.mean([r["final_score"] for r in results.values()])
        }
