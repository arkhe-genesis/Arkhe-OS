import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
import heapq
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# ============================================================================
# 1. MODELO FÍSICO DO PENTACENO COM LENTE DE TENSÃO E RUÍDO TÉRMICO
# ============================================================================

class PentaceneLens:
    """
    Cristal de pentaceno com uma "lente" de tensão de gate.

    A lente é uma região circular onde a tensão Vg varia radialmente,
    criando um gradiente de hopping que desvia a trajetória do pólaron.
    """

    def __init__(
        self,
        Nx: int = 80,           # sítios horizontais
        Ny: int = 80,           # sítios verticais
        t0: float = 0.1,        # hopping base (eV)
        lens_center: Tuple[float, float] = (0.5, 0.5),  # centro da lente (fracionário)
        lens_radius: float = 0.20,    # raio da lente (fracionário)
        lens_strength: float = 5.0,   # intensidade máxima de Vg na lente
        alpha_gate: float = 0.15,     # sensibilidade t_ij = t0 * exp(-alpha * Vg)
        thermal_noise: float = 0.0    # intensidade do ruído térmico
    ):
        self.Nx = Nx
        self.Ny = Ny
        self.t0 = t0
        self.lens_center = lens_center
        self.lens_radius = lens_radius
        self.lens_strength = lens_strength
        self.alpha_gate = alpha_gate
        self.thermal_noise = thermal_noise

        # Construir grade de tensão (lente gaussiana + ruído térmico)
        self.Vg = self._build_lens_potential()

        # Construir hoppings modificados pela lente
        self.tx, self.ty = self._compute_hoppings()

        # Métrica Riemanniana: g_xx = 1/tx², g_yy = 1/ty²
        self.g_xx, self.g_yy = self._compute_metric()

    def _build_lens_potential(self) -> np.ndarray:
        """Constrói potencial de gate com perfil de lente gaussiana e adiciona ruído térmico."""
        x = np.linspace(0, 1, self.Nx)
        y = np.linspace(0, 1, self.Ny)
        X, Y = np.meshgrid(x, y, indexing='ij')

        # Distância ao centro da lente
        R = np.sqrt((X - self.lens_center[0])**2 + (Y - self.lens_center[1])**2)

        # Perfil gaussiano: Vg máximo no centro, decai suavemente
        Vg = self.lens_strength * np.exp(-R**2 / (2 * self.lens_radius**2))

        # Ruído térmico
        if self.thermal_noise > 0:
            noise = np.random.normal(0, self.thermal_noise, size=(self.Nx, self.Ny))
            Vg += noise

        return Vg

    def _compute_hoppings(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula hoppings modificados pela lente: t = t0 * exp(-alpha * Vg_medio)."""
        # Hopping horizontal entre (i,j) e (i+1,j)
        Vg_h = (self.Vg[:-1, :] + self.Vg[1:, :]) / 2
        tx = self.t0 * np.exp(-self.alpha_gate * Vg_h)

        # Hopping vertical entre (i,j) e (i,j+1) — 50% do horizontal (anisotropia)
        Vg_v = (self.Vg[:, :-1] + self.Vg[:, 1:]) / 2
        ty = self.t0 * 0.5 * np.exp(-self.alpha_gate * Vg_v)

        return tx, ty

    def _compute_metric(self) -> Tuple[np.ndarray, np.ndarray]:
        """Métrica Riemanniana: g = 1/t² (dificuldade de tunelamento)."""
        g_xx = 1.0 / (self.tx**2 + 1e-12)
        g_yy = 1.0 / (self.ty**2 + 1e-12)
        return g_xx, g_yy

    def edge_cost(self, i: int, j: int, direction: str) -> float:
        """
        Custo de uma aresta na direção especificada.
        Custo = √(g_ij) — a distância Riemanniana por passo.
        """
        if direction == 'right' and i < self.Nx - 1:
            return np.sqrt(self.g_xx[i, j])  # custo horizontal
        elif direction == 'left' and i > 0:
            return np.sqrt(self.g_xx[i-1, j])
        elif direction == 'up' and j < self.Ny - 1:
            return np.sqrt(self.g_yy[i, j])  # custo vertical
        elif direction == 'down' and j > 0:
            return np.sqrt(self.g_yy[i, j-1])
        else:
            return float('inf')

    def neighbors(self, i: int, j: int) -> List[Tuple[int, int, float, str]]:
        """Retorna vizinhos acessíveis com custo e direção."""
        result = []
        for di, dj, direction in [(1, 0, 'right'), (-1, 0, 'left'),
                                   (0, 1, 'up'), (0, -1, 'down')]:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.Nx and 0 <= nj < self.Ny:
                cost = self.edge_cost(i, j, direction)
                result.append((ni, nj, cost, direction))
        return result

    def get_local_curvature(self, i: int, j: int) -> float:
        """Curvatura escalar local: |∇g| / g (variação relativa da métrica)."""
        if i < 1 or i >= self.Nx - 1 or j < 1 or j >= self.Ny - 1:
            return 0.0

        # Gradiente da métrica por diferenças finitas
        dgx_dx = (self.g_xx[i+1, j] - self.g_xx[i-1, j]) / 2
        dgy_dy = (self.g_yy[i, j+1] - self.g_yy[i, j-1]) / 2

        g_mean = (self.g_xx[i, j] + self.g_yy[i, j]) / 2
        return np.sqrt(dgx_dx**2 + dgy_dy**2) / (g_mean + 1e-12)


# ============================================================================
# 2. ALGORITMO DE DIJKSTRA GEODÉSICO (Multi-Pólaron)
# ============================================================================

class GeodesicDijkstra:
    """
    Algoritmo de Dijkstra para encontrar a geodésica (caminho de menor custo)
    na métrica Riemanniana do pentaceno.
    """

    def __init__(self, lens: PentaceneLens):
        self.lens = lens

    def find_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        heuristic_weight: float = 0.0,  # 0 = Dijkstra puro, >0 = A*
        dynamic_repulsion_path: Optional[List[Tuple[int, int]]] = None,
        coulomb_strength: float = 2.0
    ) -> Dict:
        """
        Encontra o caminho geodésico entre dois pontos.
        """
        Nx, Ny = self.lens.Nx, self.lens.Ny

        # Inicialização
        dist = np.full((Nx, Ny), np.inf)
        prev = np.full((Nx, Ny, 2), -1, dtype=int)
        visited = np.zeros((Nx, Ny), dtype=bool)
        steps = np.full((Nx, Ny), 0, dtype=int)

        si, sj = start
        ei, ej = end
        dist[si, sj] = 0.0

        # Heap: (custo_estimado, custo_real, i, j)
        pq = [(0.0, 0.0, si, sj)]
        nodes_explored = 0

        while pq:
            _, cost_curr, i, j = heapq.heappop(pq)

            if visited[i, j]:
                continue
            visited[i, j] = True
            nodes_explored += 1

            if (i, j) == (ei, ej):
                break

            curr_step = steps[i, j]

            for ni, nj, edge_cost, _ in self.lens.neighbors(i, j):
                if visited[ni, nj]:
                    continue

                # Calcular repulsão se houver outro pólaron
                repulsion = 0.0
                if dynamic_repulsion_path is not None:
                    # Encontrar posição do outro pólaron no mesmo passo (aproximação)
                    other_step = min(curr_step + 1, len(dynamic_repulsion_path) - 1)
                    oi, oj = dynamic_repulsion_path[other_step]

                    dist_sq = (ni - oi)**2 + (nj - oj)**2
                    if dist_sq < 1:
                        repulsion = coulomb_strength * 50.0  # Penalidade extrema se colidir
                    else:
                        repulsion = coulomb_strength / np.sqrt(dist_sq) # Repulsão de Coulomb (1/r)

                new_cost = cost_curr + edge_cost + repulsion

                # Heurística A* opcional: distância Euclidiana ao alvo
                h = 0.0
                if heuristic_weight > 0:
                    h = heuristic_weight * np.sqrt((ni - ei)**2 + (nj - ej)**2)

                if new_cost < dist[ni, nj]:
                    dist[ni, nj] = new_cost
                    prev[ni, nj] = [i, j]
                    steps[ni, nj] = curr_step + 1
                    heapq.heappush(pq, (new_cost + h, new_cost, ni, nj))

        # Reconstruir caminho
        path = []
        if not visited[ei, ej]:
            return {'path': [], 'cost': float('inf'), 'found': False, 'nodes_explored': nodes_explored}

        ci, cj = ei, ej
        while (ci, cj) != (si, sj):
            path.append((ci, cj))
            ci, cj = int(prev[ci, cj, 0]), int(prev[ci, cj, 1])
        path.append((si, sj))
        path.reverse()

        # Perfil de curvatura ao longo do caminho
        curvature_profile = [self.lens.get_local_curvature(i, j) for i, j in path]

        # Calcular a distância Euclidiana equivalente
        euclidean_dist = np.sqrt((ei - si)**2 + (ej - sj)**2)

        return {
            'path': path,
            'cost': dist[ei, ej],
            'found': True,
            'nodes_explored': nodes_explored,
            'curvature_profile': curvature_profile,
            'path_length': len(path),
            'euclidean_ratio': dist[ei, ej] / (euclidean_dist + 1e-12),
            'max_curvature': max(curvature_profile) if curvature_profile else 0.0,
            'mean_curvature': np.mean(curvature_profile) if curvature_profile else 0.0
        }

    def compare_trajectories(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        num_trials: int = 5
    ) -> Dict:
        """
        Compara diferentes trajetórias com pesos de heurística variados.
        """
        results = []
        for alpha in np.linspace(0.0, 0.5, num_trials):
            result = self.find_path(start, end, heuristic_weight=alpha)
            result['heuristic_weight'] = alpha
            results.append(result)
        return results

class MultiPolaronSystem:
    """Sistema para resolver trajetórias repulsivas de múltiplos pólarons"""
    def __init__(self, lens: PentaceneLens, coulomb_strength: float = 15.0):
        self.lens = lens
        self.coulomb_strength = coulomb_strength
        self.dijkstra = GeodesicDijkstra(lens)

    def solve_trajectories(self, start1, end1, start2, end2, iterations=3):
        # 1. Resolver caminhos independentes primeiro
        res1 = self.dijkstra.find_path(start1, end1)
        res2 = self.dijkstra.find_path(start2, end2)

        path1 = res1['path']
        path2 = res2['path']

        # 2. Iterar com repulsão mútua
        for it in range(iterations):
            # Recalcular caminho 1 com repulsão do caminho 2
            res1 = self.dijkstra.find_path(start1, end1, dynamic_repulsion_path=path2, coulomb_strength=self.coulomb_strength)
            path1 = res1['path']

            # Recalcular caminho 2 com repulsão do caminho 1 (atualizado)
            res2 = self.dijkstra.find_path(start2, end2, dynamic_repulsion_path=path1, coulomb_strength=self.coulomb_strength)
            path2 = res2['path']

        return res1, res2

# ============================================================================
# 3. VISUALIZAÇÃO
# ============================================================================

class PolarontrajectoryVisualizer:
    """Visualiza a trajetória do pólaron através da lente de pentaceno."""

    def __init__(self, lens: PentaceneLens, path_result: Dict,
                 start: Tuple[int, int], end: Tuple[int, int],
                 path_result2: Optional[Dict] = None, start2: Optional[Tuple[int, int]] = None, end2: Optional[Tuple[int, int]] = None):
        self.lens = lens
        self.path_result = path_result
        self.start = start
        self.end = end
        self.path_result2 = path_result2
        self.start2 = start2
        self.end2 = end2

    def plot_full(self, save_path: Optional[str] = None):
        """Visualização completa com 4 painéis."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 14))

        # 1. Potencial da lente + trajetória
        ax = axes[0, 0]
        im = ax.imshow(self.lens.Vg.T, origin='lower', cmap='plasma',
                       extent=[0, self.lens.Nx, 0, self.lens.Ny])
        plt.colorbar(im, ax=ax, label='Tensão de Gate Vg (V)')

        if self.path_result['found']:
            path_xy = np.array(self.path_result['path'])
            ax.plot(path_xy[:, 0], path_xy[:, 1], 'w-', linewidth=2.5, label='Pólaron 1')
            ax.plot(path_xy[::10, 0], path_xy[::10, 1], 'wo', markersize=3, alpha=0.6)

        if self.path_result2 and self.path_result2['found']:
            path_xy2 = np.array(self.path_result2['path'])
            ax.plot(path_xy2[:, 0], path_xy2[:, 1], 'k-', linewidth=2.5, label='Pólaron 2')
            ax.plot(path_xy2[::10, 0], path_xy2[::10, 1], 'ko', markersize=3, alpha=0.6)

        ax.plot(self.start[0], self.start[1], 'go', markersize=12, label='Source 1 (injeção)')
        ax.plot(self.end[0], self.end[1], 'ro', markersize=12, label='Drain 1 (coleta)')

        if self.start2 and self.end2:
            ax.plot(self.start2[0], self.start2[1], 'g^', markersize=12, label='Source 2 (injeção)')
            ax.plot(self.end2[0], self.end2[1], 'r^', markersize=12, label='Drain 2 (coleta)')

        ax.set_title('Trajetória Geodésica dos Pólarons (Com Repulsão)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.set_xlabel('Sítio i')
        ax.set_ylabel('Sítio j')

        # 2. Métrica g_xx
        ax = axes[0, 1]
        im = ax.imshow(self.lens.g_xx.T, origin='lower', cmap='inferno',
                       extent=[0, self.lens.Nx, 0, self.lens.Ny])
        plt.colorbar(im, ax=ax, label='g_xx (dificuldade de tunelamento)')

        if self.path_result['found']:
            ax.plot(path_xy[:, 0], path_xy[:, 1], 'c-', linewidth=2, alpha=0.8)
        if self.path_result2 and self.path_result2['found']:
            ax.plot(path_xy2[:, 0], path_xy2[:, 1], 'g-', linewidth=2, alpha=0.8)

        ax.plot(self.start[0], self.start[1], 'go', markersize=8)
        ax.plot(self.end[0], self.end[1], 'ro', markersize=8)
        if self.start2 and self.end2:
            ax.plot(self.start2[0], self.start2[1], 'g^', markersize=8)
            ax.plot(self.end2[0], self.end2[1], 'r^', markersize=8)
        ax.set_title('Métrica g_xx = 1/tx² (Com Ruído Térmico)', fontsize=14, fontweight='bold')

        # 3. Métrica g_yy
        ax = axes[1, 0]
        im = ax.imshow(self.lens.g_yy.T, origin='lower', cmap='inferno',
                       extent=[0, self.lens.Nx, 0, self.lens.Ny])
        plt.colorbar(im, ax=ax, label='g_yy (dificuldade de tunelamento)')

        if self.path_result['found']:
            ax.plot(path_xy[:, 0], path_xy[:, 1], 'c-', linewidth=2, alpha=0.8)
        if self.path_result2 and self.path_result2['found']:
            ax.plot(path_xy2[:, 0], path_xy2[:, 1], 'g-', linewidth=2, alpha=0.8)

        ax.plot(self.start[0], self.start[1], 'go', markersize=8)
        ax.plot(self.end[0], self.end[1], 'ro', markersize=8)
        if self.start2 and self.end2:
            ax.plot(self.start2[0], self.start2[1], 'g^', markersize=8)
            ax.plot(self.end2[0], self.end2[1], 'r^', markersize=8)
        ax.set_title('Métrica g_yy = 1/ty² (Com Ruído Térmico)', fontsize=14, fontweight='bold')

        # 4. Curvatura ao longo do caminho
        ax = axes[1, 1]
        if self.path_result['found'] and self.path_result['curvature_profile']:
            curv = self.path_result['curvature_profile']
            path_len = len(curv)
            ax.plot(range(path_len), curv, 'b-', linewidth=2, label='Curvatura P1')

            if self.path_result2 and self.path_result2['found']:
                curv2 = self.path_result2['curvature_profile']
                path_len2 = len(curv2)
                ax.plot(range(path_len2), curv2, 'g-', linewidth=2, label='Curvatura P2')

            ax.set_xlabel('Passo ao longo da geodésica', fontsize=12)
            ax.set_ylabel('Curvatura |∇g|/g', fontsize=12)
            ax.set_title('Perfil de Curvatura ao Longo da Trajetória', fontsize=14, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)

        # Informações textuais
        info_text = (
            f"Lente: centro=({self.lens.lens_center[0]:.2f}, {self.lens.lens_center[1]:.2f}), "
            f"raio={self.lens.lens_radius:.2f}, força={self.lens.lens_strength:.0f}V, ruído={self.lens.thermal_noise:.2f}\n"
            f"P1: ({self.start[0]}, {self.start[1]}) → ({self.end[0]}, {self.end[1]}) | "
            f"Custo geodésico: {self.path_result['cost']:.2f}\n"
        )
        if self.path_result2:
            info_text += f"P2: ({self.start2[0]}, {self.start2[1]}) → ({self.end2[0]}, {self.end2[1]}) | Custo geodésico: {self.path_result2['cost']:.2f}"

        fig.suptitle(info_text, fontsize=11, family='monospace', y=0.02)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()

# ============================================================================
# 4. EXECUÇÃO E DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ARKHE OS v∞.Ω.∇+++.148.1 — DIJKSTRA GEODÉSICO NO PENTACENO (MULTI-PÓLARON + RUÍDO TÉRMICO)")
    print("=" * 80)

    # Configurar lente de pentaceno com RUÍDO TÉRMICO
    lens = PentaceneLens(
        Nx=100, Ny=100,
        t0=0.1,
        lens_center=(0.5, 0.5),
        lens_radius=0.18,
        lens_strength=8.0,
        alpha_gate=0.12,
        thermal_noise=0.8
    )

    print(f"\n[LENTE] Centro: {lens.lens_center}, Raio: {lens.lens_radius}")
    print(f"[LENTE] Força máx: {lens.lens_strength:.1f}V, α_gate: {lens.alpha_gate}, Ruído térmico: {lens.thermal_noise}")

    # Ponto de injeção (source) e coleta (drain) para dois pólarons
    start1 = (20, 40)
    end1 = (80, 40)

    start2 = (20, 60)
    end2 = (80, 60)

    print(f"\n[PÓLARON 1] Source: {start1} → Drain: {end1}")
    print(f"[PÓLARON 2] Source: {start2} → Drain: {end2}")

    # Executar Sistema Multi-Pólaron
    sys = MultiPolaronSystem(lens, coulomb_strength=80.0)
    res1, res2 = sys.solve_trajectories(start1, end1, start2, end2, iterations=4)

    print(f"\n[RESULTADO P1]")
    print(f"  Caminho encontrado: {res1['found']}")
    print(f"  Custo geodésico: {res1['cost']:.2f}")
    print(f"  Passos no caminho: {res1['path_length']}")

    print(f"\n[RESULTADO P2]")
    print(f"  Caminho encontrado: {res2['found']}")
    print(f"  Custo geodésico: {res2['cost']:.2f}")
    print(f"  Passos no caminho: {res2['path_length']}")

    # Analisar deflexão mútua
    def calc_dist(p1, p2):
        return [np.sqrt((p1[min(i, len(p1)-1)][0] - p2[min(i, len(p2)-1)][0])**2 + (p1[min(i, len(p1)-1)][1] - p2[min(i, len(p2)-1)][1])**2) for i in range(max(len(p1), len(p2)))]

    if res1['found'] and res2['found']:
        dist = calc_dist(res1['path'], res2['path'])
        print(f"\n[REPULSÃO] Distância mínima entre os caminhos: {min(dist):.2f} sítios")
        print(f"[REPULSÃO] Distância média entre os caminhos: {np.mean(dist):.2f} sítios")

    # Visualizar
    viz = PolarontrajectoryVisualizer(lens, res1, start1, end1, path_result2=res2, start2=start2, end2=end2)
    viz.plot_full(save_path="polaron_geodesic_pentacene.png")

    print("\n" + "=" * 80)
    print("DIJKSTRA GEODÉSICO CONCLUÍDO")
    print("=" * 80)
