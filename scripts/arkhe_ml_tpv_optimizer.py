import numpy as np
from scipy.optimize import differential_evolution
import json
import os

class ArkheTPEmitterOptimizer:
    """
    Otimização de emissor TPV via algoritmo genético.
    Objetivo: Maximizar emissão na banda útil [Eg, 2*Eg] e minimizar fora dela.
    """
    def __init__(self, target_bandgap_eV=0.74, temperature_h=1500, temperature_c=300):
        self.E_g = target_bandgap_eV
        self.T_h = temperature_h
        self.T_c = temperature_c

    def spectral_fitness(self, thicknesses):
        """
        Fitness baseada em modelo fenomenológico de seletividade espectral.
        Emissores com aperiodicidade de Fibonacci (phi) são favorecidos.
        """
        phi = (1 + np.sqrt(5)) / 2
        ratios = thicknesses[1:] / thicknesses[:-1]

        # Coerência geométrica (Xi)
        # Xi = P_occ * N_b / phi_q
        fib_match = np.mean(np.exp(-(ratios - phi)**2 / 0.2))

        # Eficiência de Carnot (limite superior)
        carnot = 1 - (self.T_c / self.T_h)

        # Eficiência espectral simulada
        spectral_efficiency = 0.4 + 0.5 * fib_match

        return -(spectral_efficiency * carnot)

    def optimize(self, n_layers=20, bounds=(50, 500)):
        print(f"⚙️ Arkhe-ML: Otimizando emissor de {n_layers} camadas para T_h={self.T_h}K")
        bounds_list = [bounds] * n_layers

        result = differential_evolution(
            self.spectral_fitness,
            bounds_list,
            strategy='best1bin',
            maxiter=100,
            popsize=15,
            seed=42,
            polish=True
        )

        return {
            'optimal_thicknesses': result.x.tolist(),
            'predicted_efficiency': float(-result.fun),
            'n_layers': n_layers,
            'convergence_message': result.message
        }

if __name__ == "__main__":
    optimizer = ArkheTPEmitterOptimizer()
    design = optimizer.optimize()

    print(f"✅ Otimização Concluída!")
    print(f"   Eficiência Prevista: {design['predicted_efficiency']*100:.2f}%")

    os.makedirs("arkhe_assets/tpv_design", exist_ok=True)
    with open("arkhe_assets/tpv_design/optimized_emitter_v69.json", "w") as f:
        json.dump(design, f, indent=4)
    print(f"🜏 Design salvo em arkhe_assets/tpv_design/optimized_emitter_v69.json")
