import math

class TraversableWormholeEngine:
    def __init__(self, q, g, Nf, lp=1.0):
        self.q = q
        self.g = g
        self.Nf = Nf
        self.lp = lp

    def calculate_geometry(self):
        # Raio extremal: r_e = q * √(π) / g
        re = self.q * math.sqrt(math.pi) / self.g

        # Comprimento da garganta: ℓ = r_e * (16 * π * q) / (Nf * g²)
        throat_length = re * (16.0 * math.pi * self.q) / (self.Nf * self.g**2)

        # Energia de ligação: E_b = - 1 / (4ℓ)
        binding_energy = -1.0 / (4.0 * throat_length)

        # Gap de energia: ΔE = 4 |E_b|
        energy_gap = 4.0 * abs(binding_energy)

        # Entropia: S = π² * q² / g²
        entropy = (math.pi**2 * self.q**2) / self.g**2

        # Parâmetro de estabilidade: σ = (2 * q * √(π)) / (g * ℓ²)
        stability = (2.0 * self.q * math.sqrt(math.pi)) / (self.g * throat_length**2)

        # Frequência orbital: ω = σ / ℓ
        orbital_frequency = stability / throat_length

        # Tempo de vida: τ = ℓ³ / q²
        lifetime = (throat_length**3) / (self.q**2)

        # Validade: regime quântico (g² * Nf > 1) and distância (ℓ < re * q²)
        quantum_regime_valid = (self.g**2 * self.Nf > 1.0)
        distance_valid = (throat_length < re * self.q**2)
        is_valid = quantum_regime_valid and distance_valid

        return {
            "re": re,
            "throat_length": throat_length,
            "binding_energy": binding_energy,
            "energy_gap": energy_gap,
            "entropy": entropy,
            "orbital_frequency": orbital_frequency,
            "lifetime": lifetime,
            "stability_parameter": stability,
            "is_valid": is_valid
        }
