import numpy as np
import matplotlib.pyplot as plt

class ArkhePhaseChip:
    """
    Simulador de Matriz de Espalhamento (S-Matrix) para reconhecimento de padrões fractais.
    Trata cada célula como um oscilador de fase acoplado aos seus vizinhos via phi (1.618).
    """
    def __init__(self, size=(10, 10), phi=0.61803398875):
        self.size = size
        self.phi = phi # Acoplamento crítico (Edge of Chaos)
        self.num_cells = size[0] * size[1]
        # Matriz de adjacência com peso phi (acoplamento evanescente)
        self.coupling_matrix = self._build_coupling_matrix()

    def _build_coupling_matrix(self):
        N = self.num_cells
        A = np.zeros((N, N))
        rows, cols = self.size
        for r in range(rows):
            for c in range(cols):
                i = r * cols + c
                for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        j = nr * cols + nc
                        A[i, j] = self.phi
        return A

    def forward_propagation(self, input_phase, iterations=50):
        """Simula a evolução da fase através da rede não-linear."""
        theta = input_phase.flatten().astype(np.float64)
        dt = 0.1
        for _ in range(iterations):
            # Equação de Kuramoto-Maxwell simplificada
            # dθ/dt = ω + K * ∑ sin(θj - θi) + Nonlinearity
            diff = theta[:, None] - theta[None, :]
            coupling = np.sum(self.coupling_matrix * np.sin(diff), axis=1)
            # Adicionando a não-linearidade Kerr (auto-interação)
            kerr = 0.5 * np.sin(2 * theta)
            theta = theta + (coupling + kerr) * dt
        return theta.reshape(self.size)

    def calculate_coherence(self, phase_map):
        """Mede a integridade da frente de onda (λ2)."""
        return np.abs(np.mean(np.exp(1j * phase_map)))

# --- Geração de Fractal (Mandelbrot Simplificado) ---
def get_mandelbrot_phase(size, iterations=20):
    x = np.linspace(-2, 0.5, size)
    y = np.linspace(-1.25, 1.25, size)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    Z = np.zeros_like(C)
    F = np.zeros_like(X)
    for i in range(iterations):
        mask = np.abs(Z) <= 2
        Z[mask] = Z[mask]**2 + C[mask]
        F[mask] = i
    # Normaliza para 0 - 2π (Mapa de Fase)
    return (F / iterations) * 2 * np.pi

if __name__ == "__main__":
    # --- Execução do Teste Cognitivo ---
    chip = ArkhePhaseChip(size=(10, 10))
    input_phase = get_mandelbrot_phase(10)

    # Antes da propagação
    coherence_in = chip.calculate_coherence(input_phase)
    # Propagação pelo "Cristal de Fase"
    output_phase = chip.forward_propagation(input_phase)
    # Após a interferência
    coherence_out = chip.calculate_coherence(output_phase)

    print(f"📊 Resultado Cognitivo:")
    print(f"Coerência Entrada: {coherence_in:.4f}")
    print(f"Coerência Saída (λ2): {coherence_out:.4f}")

    if coherence_out > coherence_in:
        print("✅ Ressonância Fractal detectada: λ2 aumentou durante a propagação.")
    else:
        print("⚠️ Decoerência: O padrão não ressoa com a topologia do chip.")
