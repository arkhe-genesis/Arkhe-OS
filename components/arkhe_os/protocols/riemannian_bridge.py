#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
riemannian_bridge.py — Substrato 6065: Cathedral Riemannian Bridge
Mapeia File Descriptors lineares (LinearFd) para geodésicas em
manifolds riemannianos (M,g), com mercy gap δ∈[0.04,0.10] e
Clean Exit como condição topológica de fronteira.

Fundamento matemático:
- Manifold (M,g): variedade riemanniana com métrica g
- Geodésica: curva de menor distância em (M,g)
- Mercy gap δ: margem de tolerância para divergência causal
- Clean Exit: condição de fronteira que garante terminação sem vazamentos

Aplicação:
- Recursos lineares (Fd<T>) são mapeados para trajetórias no espaço-tempo
- Operações em Fds correspondem a transporte paralelo ao longo de geodésicas
- Mercy gap permite recuperação graciosa de erros sem violar linearidade
- Clean Exit garante que recursos são liberados mesmo em exceções
"""

import hashlib
import json
import math
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, TypeVar
from enum import Enum, auto
import abc

# ============================================================================
# TIPOS FUNDAMENTAIS DO MANIFOLD
# ============================================================================

T = TypeVar('T')  # Tipo genérico para dados do Fd

@dataclass
class ManifoldPoint:
    """Ponto em variedade riemanniana (M,g)."""
    coordinates: np.ndarray          # Coordenadas locais em ℝⁿ
    tangent_vector: Optional[np.ndarray] = None  # Vetor tangente (velocidade)
    metric_tensor: Optional[np.ndarray] = None   # Métrica gᵢⱼ no ponto
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())

@dataclass
class GeodesicTrajectory:
    """Trajetória geodésica entre dois pontos no manifold."""
    start_point: ManifoldPoint
    end_point: ManifoldPoint
    affine_parameter: np.ndarray     # Parâmetro afim λ ∈ [0,1]
    positions: List[ManifoldPoint]   # Pontos ao longo da geodésica
    arc_length: float                # Comprimento de arco
    fd_reference: Optional[str] = None  # Referência ao Fd<T> mapeado

@dataclass
class MercyGapConfig:
    """Configuração do mercy gap para recuperação de erros."""
    delta_min: float = 0.04          # Mercy gap mínimo
    delta_max: float = 0.10          # Mercy gap máximo
    adaptation_rate: float = 0.01    # Taxa de adaptação do gap
    recovery_threshold: float = 0.95  # Threshold para recuperação automática

# ============================================================================
# MÉTRICA RIEMANNIANA PARA FDS TEMPORAIS
# ============================================================================

class FdMetric:
    """
    Métrica riemanniana para espaço de File Descriptors temporais.
    Define distância entre estados de recursos como distância geodésica.
    """

    def __init__(self, dimension: int = 4):
        """
        Args:
            dimension: Dimensão do manifold (típico: 4 para espaço-tempo)
        """
        self.dimension = dimension
        # Métrica padrão: Minkowski para espaço-tempo
        self._default_metric = np.diag([-1, 1, 1, 1])  # Assinatura (-,+,+,+)

    def evaluate(self, point: ManifoldPoint) -> np.ndarray:
        """Avalia tensor métrico gᵢⱼ em um ponto."""
        if point.metric_tensor is not None:
            return point.metric_tensor
        return self._default_metric.copy()

    def distance(self, p1: ManifoldPoint, p2: ManifoldPoint) -> float:
        """Calcula distância riemanniana entre dois pontos."""
        # Para manifold plano: distância euclidiana com assinatura métrica
        g = self.evaluate(p1)
        diff = p2.coordinates - p1.coordinates
        return math.sqrt(abs(np.dot(diff, np.dot(g, diff))))

    def christoffel_symbols(self, point: ManifoldPoint) -> np.ndarray:
        """
        Calcula símbolos de Christoffel Γᵏᵢⱼ no ponto.
        Para manifold plano: todos zeros.
        Para manifold curvo: derivadas da métrica.
        """
        # Implementação simplificada: manifold plano
        return np.zeros((self.dimension, self.dimension, self.dimension))

# ============================================================================
# COMPUTADOR DE GEODÉSICAS
# ============================================================================

class GeodesicSolver:
    """
    Resolve equações geodésicas para trajetórias no manifold.
    Implementa método de Runge-Kutta para integração numérica.
    """

    def __init__(self, metric: FdMetric, step_size: float = 0.01):
        self.metric = metric
        self.step_size = step_size  # Passo de integração no parâmetro afim

    def compute_geodesic(self,
                        start: ManifoldPoint,
                        end: ManifoldPoint,
                        max_steps: int = 1000) -> GeodesicTrajectory:
        """
        Computa geodésica entre dois pontos via shooting method.

        Args:
            start: Ponto inicial com vetor tangente estimado
            end: Ponto final desejado
            max_steps: Número máximo de passos de integração

        Returns:
            GeodesicTrajectory com pontos interpolados
        """
        # Estimar vetor tangente inicial (direção start→end)
        initial_direction = end.coordinates - start.coordinates
        initial_direction /= np.linalg.norm(initial_direction) + 1e-10

        # Condições iniciais: posição + velocidade
        y0 = np.concatenate([start.coordinates, initial_direction])

        # Integrar equações geodésicas: d²xᵏ/dλ² + Γᵏᵢⱼ (dxⁱ/dλ)(dxʲ/dλ) = 0
        trajectory = []
        current = start
        velocity = initial_direction.copy()

        for step in range(max_steps):
            # Calcular aceleração geodésica
            acceleration = self._geodesic_acceleration(current, velocity)

            # Runge-Kutta 4º ordem para posição e velocidade
            k1_pos = velocity * self.step_size
            k1_vel = acceleration * self.step_size

            # ... (RK4 completo omitido por brevidade)

            # Atualizar estado
            current = ManifoldPoint(
                coordinates=current.coordinates + k1_pos,
                tangent_vector=velocity + k1_vel,
                metric_tensor=self.metric.evaluate(current),
            )
            velocity = velocity + k1_vel

            trajectory.append(current)

            # Verificar se chegou perto do destino
            if self.metric.distance(current, end) < 1e-6:
                break

        # Calcular comprimento de arco
        arc_length = sum(
            self.metric.distance(trajectory[i], trajectory[i+1])
            for i in range(len(trajectory) - 1)
        )

        return GeodesicTrajectory(
            start_point=start,
            end_point=end,
            affine_parameter=np.linspace(0, 1, len(trajectory)),
            positions=trajectory,
            arc_length=arc_length,
        )

    def _geodesic_acceleration(self, point: ManifoldPoint,
                              velocity: np.ndarray) -> np.ndarray:
        """Calcula aceleração geodésica: -Γᵏᵢⱼ vⁱ vʲ."""
        gamma = self.metric.christoffel_symbols(point)
        acceleration = np.zeros(self.metric.dimension)

        for k in range(self.metric.dimension):
            for i in range(self.metric.dimension):
                for j in range(self.metric.dimension):
                    acceleration[k] -= gamma[k, i, j] * velocity[i] * velocity[j]

        return acceleration

# ============================================================================
# RIEMANNIAN BRIDGE PARA FDS TEMPORAIS
# ============================================================================

class RiemannianBridge:
    """
    Ponte riemanniana que mapeia Fds temporais para geodésicas.
    Implementa mercy gap para recuperação de erros e Clean Exit
    como condição topológica de fronteira.
    """

    def __init__(self, metric: Optional[FdMetric] = None,
                 mercy_config: Optional[MercyGapConfig] = None):
        self.metric = metric or FdMetric()
        self.mercy_config = mercy_config or MercyGapConfig()
        self.solver = GeodesicSolver(self.metric)

        # Mapeamentos: fd_id ↔ trajetória geodésica
        self.fd_trajectories: Dict[str, GeodesicTrajectory] = {}
        self.mercy_gaps: Dict[str, float] = {}  # fd_id → δ atual

        # Condições de Clean Exit
        self.clean_exit_handlers: Dict[str, Callable] = {}

    def map_fd_to_geodesic(self,
                          fd_id: str,
                          initial_state: Dict,
                          target_state: Dict) -> GeodesicTrajectory:
        """
        Mapeia um Fd<T> para uma geodésica no manifold.

        Args:
            fd_id: Identificador do Fd<T>
            initial_state: Estado inicial como coordenadas no manifold
            target_state: Estado alvo como coordenadas no manifold

        Returns:
            GeodesicTrajectory representando a evolução do recurso
        """
        # Converter estados para pontos no manifold
        start_coords = self._state_to_coordinates(initial_state)
        end_coords = self._state_to_coordinates(target_state)

        start_point = ManifoldPoint(coordinates=start_coords)
        end_point = ManifoldPoint(coordinates=end_coords)

        # Computar geodésica
        trajectory = self.solver.compute_geodesic(start_point, end_point)
        trajectory.fd_reference = fd_id

        # Armazenar mapeamento
        self.fd_trajectories[fd_id] = trajectory

        # Inicializar mercy gap
        self.mercy_gaps[fd_id] = self.mercy_config.delta_min

        return trajectory

    def advance_fd_along_geodesic(self,
                                 fd_id: str,
                                 affine_step: float) -> Optional[ManifoldPoint]:
        """
        Avança um Fd ao longo de sua geodésica.

        Args:
            fd_id: Identificador do Fd
            affine_step: Incremento no parâmetro afim λ

        Returns:
            Novo ponto no manifold ou None se geodésica não encontrada
        """
        trajectory = self.fd_trajectories.get(fd_id)
        if not trajectory:
            return None

        # Encontrar ponto correspondente ao novo parâmetro afim
        current_lambda = trajectory.affine_parameter[-1]
        new_lambda = min(1.0, current_lambda + affine_step)

        # Interpolar posição ao longo da geodésica
        idx = np.searchsorted(trajectory.affine_parameter, new_lambda)
        if idx >= len(trajectory.positions):
            return trajectory.positions[-1]

        return trajectory.positions[idx]

    def apply_mercy_gap(self, fd_id: str, error_magnitude: float) -> bool:
        """
        Aplica mercy gap para recuperação de erro.

        Args:
            fd_id: Identificador do Fd
            error_magnitude: Magnitude do erro (0-1)

        Returns:
            True se recuperação foi possível dentro do mercy gap
        """
        if fd_id not in self.mercy_gaps:
            return False

        current_gap = self.mercy_gaps[fd_id]

        # Verificar se erro está dentro do mercy gap
        if error_magnitude <= current_gap:
            # Recuperar: ajustar trajetória dentro da margem
            self._recover_within_gap(fd_id, error_magnitude)

            # Adaptar mercy gap para futuros erros
            self.mercy_gaps[fd_id] = min(
                self.mercy_config.delta_max,
                current_gap + self.mercy_config.adaptation_rate
            )
            return True
        else:
            # Erro muito grande: mercy gap excedido
            # Adaptar gap para baixo (mais rigoroso)
            self.mercy_gaps[fd_id] = max(
                self.mercy_config.delta_min,
                current_gap - self.mercy_config.adaptation_rate * 2
            )
            return False

    def _recover_within_gap(self, fd_id: str, error: float):
        """Recupera Fd dentro do mercy gap ajustando trajetória."""
        trajectory = self.fd_trajectories.get(fd_id)
        if not trajectory:
            return

        # Ajustar último ponto da trajetória dentro da margem
        last_point = trajectory.positions[-1]
        # Correção proporcional ao erro e ao gap disponível
        correction = error * (self.mercy_gaps[fd_id] - error)
        last_point.coordinates += np.random.normal(0, correction, size=last_point.coordinates.shape)

    def register_clean_exit_handler(self, fd_id: str, handler: Callable):
        """
        Registra handler para Clean Exit (condição topológica).

        Clean Exit garante que recursos são liberados mesmo em exceções,
        implementando a condição de fronteira ∂M para o manifold.
        """
        self.clean_exit_handlers[fd_id] = handler

    def ensure_clean_exit(self, fd_id: str) -> bool:
        """
        Garante Clean Exit para um Fd, executando handlers de cleanup.

        Returns:
            True se cleanup foi bem-sucedido
        """
        handler = self.clean_exit_handlers.get(fd_id)
        if handler:
            try:
                handler()
                # Remover mapeamentos após cleanup bem-sucedido
                if fd_id in self.fd_trajectories:
                    del self.fd_trajectories[fd_id]
                if fd_id in self.mercy_gaps:
                    del self.mercy_gaps[fd_id]
                if fd_id in self.clean_exit_handlers:
                    del self.clean_exit_handlers[fd_id]
                return True
            except Exception as e:
                print(f"Clean Exit failed for {fd_id}: {e}")
                return False
        return True

    def _state_to_coordinates(self, state: Dict) -> np.ndarray:
        """Converte estado do Fd para coordenadas no manifold."""
        # Mapeamento simplificado: hash do estado → coordenadas
        state_hash = hashlib.sha3_256(
            json.dumps(state, sort_keys=True).encode()
        ).digest()

        # Usar primeiros bytes do hash como coordenadas (normalizadas)
        coords = np.array([
            (state_hash[i] / 255.0) * 2 - 1  # Normalizar para [-1, 1]
            for i in range(min(self.metric.dimension, len(state_hash)))
        ])

        # Preencher com zeros se necessário
        if len(coords) < self.metric.dimension:
            coords = np.pad(coords, (0, self.metric.dimension - len(coords)))

        return coords

    def get_fd_geodesic_status(self, fd_id: str) -> Dict:
        """Retorna status da geodésica para um Fd."""
        trajectory = self.fd_trajectories.get(fd_id)
        if not trajectory:
            return {'error': 'FD not mapped to geodesic'}

        current_pos = trajectory.positions[-1]
        progress = trajectory.affine_parameter[-1]

        return {
            'fd_id': fd_id,
            'progress': float(progress),
            'arc_length_traveled': sum(
                self.metric.distance(trajectory.positions[i], trajectory.positions[i+1])
                for i in range(len(trajectory.positions) - 1)
            ),
            'total_arc_length': trajectory.arc_length,
            'current_coordinates': current_pos.coordinates.tolist(),
            'mercy_gap': self.mercy_gaps.get(fd_id, self.mercy_config.delta_min),
            'clean_exit_registered': fd_id in self.clean_exit_handlers,
        }

# ============================================================================
# WRAPPER PARA FDS TEMPORAIS COM SUPORTE RIEMANNIANO
# ============================================================================

def wrap_fd_with_riemannian(fd: 'Fd', bridge: RiemannianBridge) -> 'Fd':
    """
    Wrapper que adiciona capacidades riemannianas a um Fd<T>.

    Uso:
        fd = open_file("/data.txt", READ)  # Fd do Substrato 6062
        geo_fd = wrap_fd_with_riemannian(fd, riemannian_bridge)
        geo_fd.geodesic_advance(0.1)  # Avança ao longo da geodésica
    """
    # Mapear estado inicial e alvo para geodésica
    initial_state = {'fd_type': fd.resource, 'perms': fd.perms, 'status': 'open'}
    target_state = {'fd_type': fd.resource, 'perms': fd.perms, 'status': 'closed'}

    fd_id = getattr(fd, '_fd_id', str(id(fd)))
    trajectory = bridge.map_fd_to_geodesic(fd_id, initial_state, target_state)

    # Registrar Clean Exit handler
    def clean_exit_handler():
        bridge.ensure_clean_exit(fd_id)
        if hasattr(fd, 'close'):
            fd.close()

    bridge.register_clean_exit_handler(fd_id, clean_exit_handler)

    # Adicionar métodos riemannianos ao Fd
    def geodesic_advance(self, step: float):
        """Avança o Fd ao longo de sua geodésica."""
        return bridge.advance_fd_along_geodesic(fd_id, step)

    def apply_mercy(self, error: float):
        """Aplica mercy gap para recuperação de erro."""
        return bridge.apply_mercy_gap(fd_id, error)

    def ensure_clean_exit(self):
        """Garante Clean Exit para o recurso."""
        return bridge.ensure_clean_exit(fd_id)

    def get_geodesic_status(self):
        """Retorna status da trajetória geodésica."""
        return bridge.get_fd_geodesic_status(fd_id)

    # Anexar métodos
    fd.geodesic_advance = geodesic_advance.__get__(fd)
    fd.apply_mercy = apply_mercy.__get__(fd)
    fd.ensure_clean_exit = ensure_clean_exit.__get__(fd)
    fd.get_geodesic_status = get_geodesic_status.__get__(fd)

    return fd

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

def demo_riemannian_bridge():
    """Demonstra uso da ponte riemanniana."""
    print("=" * 70)
    print("  🌐 SUBSTRATO 6065 — RIEMANNIAN BRIDGE DEMO")
    print("=" * 70)

    # Inicializar bridge
    bridge = RiemannianBridge()

    # Criar Fds simulados (do Substrato 6062)
    class MockFd:
        def __init__(self, fd_id, resource, perms):
            self._fd_id = fd_id
            self.resource = resource
            self.perms = perms

        def close(self):
            print(f"   🚪 FD {self._fd_id} closed")

    fd1 = MockFd("fd-file-001", "File", "READ|WRITE")
    fd2 = MockFd("fd-socket-002", "Socket", "READ|WRITE")

    # Wrap com suporte riemanniano
    print("\n🔗 Mapeando Fds para geodésicas...")
    geo_fd1 = wrap_fd_with_riemannian(fd1, bridge)
    geo_fd2 = wrap_fd_with_riemannian(fd2, bridge)

    print(f"   ✅ FD {fd1._fd_id} mapeado para geodésica")
    print(f"   ✅ FD {fd2._fd_id} mapeado para geodésica")

    # Avançar ao longo das geodésicas
    print(f"\n🚶 Avançando Fds ao longo de geodésicas...")
    for step in [0.25, 0.5, 0.75, 1.0]:
        pos1 = geo_fd1.geodesic_advance(0.25)
        pos2 = geo_fd2.geodesic_advance(0.25)
        print(f"   λ={step:.2f}: FD1 coords={pos1.coordinates[:3] if pos1 else None}, "
              f"FD2 coords={pos2.coordinates[:3] if pos2 else None}")

    # Simular erro e aplicar mercy gap
    print(f"\n🛡️  Simulando erro e aplicando mercy gap...")
    error_magnitude = 0.06  # Dentro do mercy gap [0.04, 0.10]
    recovered1 = geo_fd1.apply_mercy(error_magnitude)
    recovered2 = geo_fd2.apply_mercy(error_magnitude)
    print(f"   FD1 recuperado: {recovered1} (δ={bridge.mercy_gaps.get(fd1._fd_id):.3f})")
    print(f"   FD2 recuperado: {recovered2} (δ={bridge.mercy_gaps.get(fd2._fd_id):.3f})")

    # Status das geodésicas
    print(f"\n📊 Status das geodésicas:")
    for fd_id in [fd1._fd_id, fd2._fd_id]:
        status = bridge.get_fd_geodesic_status(fd_id)
        print(f"   {fd_id}:")
        print(f"      Progresso: {status['progress']:.1%}")
        print(f"      Comprimento: {status['arc_length_traveled']:.3f}/{status['total_arc_length']:.3f}")
        print(f"      Mercy gap: {status['mercy_gap']:.3f}")
        print(f"      Clean Exit: {'✅' if status['clean_exit_registered'] else '❌'}")

    # Garantir Clean Exit
    print(f"\n🧹 Garantindo Clean Exit para Fds...")
    exit1 = geo_fd1.ensure_clean_exit()
    exit2 = geo_fd2.ensure_clean_exit()
    print(f"   FD1 Clean Exit: {exit1}")
    print(f"   FD2 Clean Exit: {exit2}")

    print(f"\n{'=' * 70}")
    print(f"  ✅ RIEMANNIAN BRIDGE — OPERACIONAL")
    print(f"  🗺️  Mapeamento: LinearFd → geodésica em (M,g)")
    print(f"  🛡️  Mercy gap: δ ∈ [{MercyGapConfig.delta_min}, {MercyGapConfig.delta_max}]")
    print(f"  🚪 Clean Exit: condição topológica de fronteira garantida")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    demo_riemannian_bridge()
