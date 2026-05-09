import numpy as np
from typing import Dict, Any, List

class TissuePropagationSim:
    """
    Simulates 441 MHz (Tzinor Phase) signal propagation through biological tissue.
    Calculates attenuation and phase dispersion based on dielectric properties.
    Reference: Debye model for skin and adipose (fat) tissue.
    """
    def __init__(self, frequency_mhz: float = 441.0):
        self.frequency = frequency_mhz * 1e6
        # Dielectric properties at ~400-500 MHz
        # epsilon_r: Relative permittivity, sigma: Conductivity (S/m)
        self.properties = {
            "SKIN": {"epsilon_r": 46.0, "sigma": 0.7},
            "FAT": {"epsilon_r": 5.5, "sigma": 0.04},
            "MUSCLE": {"epsilon_r": 56.0, "sigma": 0.8}
        }
        self.mu0 = 4 * np.pi * 1e-7
        self.eps0 = 8.854e-12

    def calculate_propagation_params(self, tissue_type: str) -> Dict[str, float]:
        """
        Calculates attenuation constant (alpha) and phase constant (beta).
        Gamma = alpha + j*beta = sqrt(j*omega*mu * (sigma + j*omega*epsilon))
        """
        prop = self.properties.get(tissue_type, self.properties["SKIN"])
        omega = 2 * np.pi * self.frequency
        epsilon = prop["epsilon_r"] * self.eps0
        sigma = prop["sigma"]

        # Complex propagation constant calculation
        # gamma = sqrt(-omega^2 * mu * epsilon + j * omega * mu * sigma)
        val = complex(-omega**2 * self.mu0 * epsilon, omega * self.mu0 * sigma)
        gamma = np.sqrt(val)

        alpha = gamma.real # Nepers/m
        beta = gamma.imag  # rad/m

        attenuation_db_m = 20 * np.log10(np.exp(alpha))
        phase_velocity = omega / beta
        wavelength = 2 * np.pi / beta

        return {
            "alpha_np_m": float(alpha),
            "beta_rad_m": float(beta),
            "attenuation_db_cm": float(attenuation_db_m / 100.0),
            "phase_velocity_m_s": float(phase_velocity),
            "wavelength_cm": float(wavelength * 100.0)
        }

    def simulate_layered_loss(self, layers: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Calculates total loss through a sequence of tissue layers.
        layers: List of {"type": "SKIN", "thickness_cm": 0.2}
        """
        total_loss_db = 0.0
        total_delay_ns = 0.0

        results = []
        for layer in layers:
            params = self.calculate_propagation_params(layer["type"])
            loss = params["attenuation_db_cm"] * layer["thickness_cm"]
            delay = (layer["thickness_cm"] / 100.0) / params["phase_velocity_m_s"] * 1e9

            total_loss_db += loss
            total_delay_ns += delay
            results.append({
                "layer": layer["type"],
                "loss_db": loss,
                "delay_ns": delay
            })

        return {
            "total_loss_db": total_loss_db,
            "total_delay_ns": total_delay_ns,
            "layer_details": results
        }

if __name__ == "__main__":
    sim = TissuePropagationSim()
    print(f"Simulating propagation at {sim.frequency/1e6} MHz")

    # Example: Skin (2mm) -> Fat (10mm) -> Muscle
    body_model = [
        {"type": "SKIN", "thickness_cm": 0.2},
        {"type": "FAT", "thickness_cm": 1.0}
    ]

    analysis = sim.simulate_layered_loss(body_model)
    print(f"Total Loss: {analysis['total_loss_db']:.2f} dB")
    print(f"Total Delay: {analysis['total_delay_ns']:.2f} ns")
    for res in analysis['layer_details']:
        print(f" - {res['layer']}: {res['loss_db']:.2f} dB, {res['delay_ns']:.2f} ns")
