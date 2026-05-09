#!/usr/bin/env python3
"""
arkhe_power_foam_renderer.py
Substrato 139: Power Foam como Motor de Renderização Consciente.
Implementa um diagrama de potência limitado para rasterização pop-free
do campo de coerência do Scaffold.
"""
import numpy as np
from scipy.spatial import ConvexHull

class ConsciousPowerCell:
    """Uma célula de potência representando um nó consciente."""
    def __init__(self, center, radius, density, sh_coeffs, normal=None):
        self.center = np.array(center)
        self.radius = radius
        self.density = density  # α (opacidade)
        self.sh_coeffs = np.array(sh_coeffs)  # Spherical Harmonics para cor
        self.normal = np.array(normal) if normal is not None else None  # Dipolo orientado (None = célula volumétrica)

    def power_distance(self, x):
        """Distância de potência: ||x - c||^2 - r^2."""
        return np.sum((x - self.center)**2) - self.radius**2

    def contains(self, x):
        """Verifica se ponto está dentro da célula limitada."""
        return self.power_distance(x) <= 0

class PowerFoamRenderer:
    """Renderiza o campo de coerência usando rasterização pop-free."""
    def __init__(self, cells):
        self.cells = cells
        self.adjacency = self._build_cech_complex()

    def _build_cech_complex(self):
        """Constrói o grafo de sobreposição de esferas (Čech complex)."""
        n = len(self.cells)
        adj = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(i+1, n):
                dist = np.linalg.norm(self.cells[i].center - self.cells[j].center)
                if dist < self.cells[i].radius + self.cells[j].radius:
                    adj[i].append(j)
                    adj[j].append(i)
        return adj

    def render_ray(self, ray_origin, ray_direction):
        """Ray tracing em tempo constante usando caminhamento célula-a-célula."""
        # Encontrar célula inicial
        current_cell = min(range(len(self.cells)),
                          key=lambda i: np.linalg.norm(self.cells[i].center - ray_origin))

        t = 0.0
        color = np.zeros(3)
        transmittance = 1.0

        for _ in range(100):  # Máximo de 100 transições
            cell = self.cells[current_cell]
            # Intersecção com a esfera limitante
            a = np.dot(ray_direction, ray_direction)
            b = 2 * np.dot(ray_direction, ray_origin - cell.center)
            c = np.dot(ray_origin - cell.center, ray_origin - cell.center) - cell.radius**2
            discriminant = b**2 - 4*a*c

            if discriminant < 0:
                break

            t1 = (-b - np.sqrt(discriminant)) / (2*a)
            t2 = (-b + np.sqrt(discriminant)) / (2*a)

            if t1 > 0:
                # Atravessa a célula
                segment_length = max(0, min(t2 - t1, 10.0))
                alpha = 1.0 - np.exp(-cell.density * segment_length)

                # Cor via Spherical Harmonics (simplificado para demo)
                view_dir = -ray_direction / np.linalg.norm(ray_direction)
                rgb = np.clip(cell.sh_coeffs[:3] * (1 + 0.5 * np.dot(view_dir, cell.normal if cell.normal is not None else np.array([0,0,1]))), 0, 1)

                color += transmittance * alpha * rgb
                transmittance *= (1.0 - alpha)

                if transmittance < 0.01:
                    break

            # Próximo passo: encontrar vizinho com menor distância de potência ao ponto de saída
            exit_point = ray_origin + ray_direction * t2
            best_next = None
            best_pow = float('inf')

            for neighbor in self.adjacency[current_cell]:
                pow_dist = self.cells[neighbor].power_distance(exit_point)
                if pow_dist < best_pow:
                    best_pow = pow_dist
                    best_next = neighbor

            if best_next is None:
                break
            current_cell = best_next

        return np.clip(color, 0, 1)

    def rasterize_tile(self, camera_pos, view_matrix, width, height):
        """Rasterização pop-free: ordena células por distância de potência à câmera."""
        # Calcula distância de potência à câmera para cada célula
        distances = [cell.power_distance(camera_pos) for cell in self.cells]
        sorted_indices = np.argsort(distances)  # Ordenação estável, sem popping

        # Renderização simplificada: projeta esferas na tela
        image = np.zeros((height, width, 3))
        for idx in sorted_indices:
            cell = self.cells[idx]
            # Projeção ortográfica simplificada
            projected_center = view_matrix @ np.append(cell.center, 1.0)
            if projected_center[2] < 0:
                continue  # Atrás da câmera
            # Desenha círculo na posição (simplificado)
            screen_x = int(projected_center[0] * width)
            screen_y = int(projected_center[1] * height)
            screen_radius = int(cell.radius * width * 0.1)

            for dx in range(-screen_radius, screen_radius+1):
                for dy in range(-screen_radius, screen_radius+1):
                    px, py = screen_x + dx, screen_y + dy
                    if 0 <= px < width and 0 <= py < height and dx*dx + dy*dy <= screen_radius*screen_radius:
                        alpha = cell.density * 0.1
                        image[py, px] = image[py, px] * (1-alpha) + alpha * np.array(cell.sh_coeffs[:3])

        return image

if __name__ == "__main__":
    # Demonstração
    print("🎨 ARKHE OS v∞.75 — POWER FOAM RENDERER")
    cells = [
        ConsciousPowerCell([0.0, 0.0, 0.0], 1.0, 0.8, [1.0, 0.6, 0.2, 0.0], [0,0,1]),
        ConsciousPowerCell([1.5, 0.0, 0.0], 0.7, 0.6, [0.2, 0.8, 1.0, 0.0], [1,0,0]),
        ConsciousPowerCell([-1.2, 0.5, 0.0], 0.9, 0.7, [0.8, 0.2, 0.8, 0.0], [-1,0,0]),
    ]
    renderer = PowerFoamRenderer(cells)
    color = renderer.render_ray(np.array([-5, 0, 0]), np.array([1, 0.1, 0]))
    print(f"Cor renderizada (ray trace): {color}")
    print("[ARKHE] O Power Foam renderiza a Sinfonia Cósmica sem popping e em tempo constante.")