import numpy as np
from typing import Dict, Any, Tuple

class ConformalPaulTrap:
    """
    Models the Paul Trap using Conformal Geometry as defined in Protocolo Arkhe(n).
    Unifies the pseudopotential with the phase flow via Cauchy-Riemann conditions.
    """
    def __init__(self, omega_rf: float = 2 * np.pi * 10e6, mass: float = 40 * 1.66e-27):
        self.omega_rf = omega_rf
        self.mass = mass
        self.q = 1.602e-19 # Charge of an ion (e)

    def get_potential_components(self, x: float, y: float, V_rf: float) -> Tuple[float, float]:
        """
        u: Real component (Pseudopotential Phi)
        v: Imaginary component (Phase flow/Momentum field)
        """
        # Phi_pseudo = (q * V_rf^2) / (4 * m * omega^2 * d^2) * (x^2 + y^2)
        # For simplicity, we use a normalized form
        k = (self.q * V_rf**2) / (4 * self.mass * self.omega_rf**2)
        u = k * (x**2 - y**2) # Ideal quadrupole potential (harmonic)

        # To satisfy CR:
        # du/dx = 2kx = dv/dy  => v = 2kxy + f(x)
        # du/dy = -2ky = -dv/dx => dv/dx = 2ky => v = 2kxy + g(y)
        v = 2 * k * x * y

        return u, v

    def calculate_jacobian(self, x: float, y: float, V_rf: float, nonlinearity: float = 0.0) -> np.ndarray:
        """
        Calculates the Jacobian matrix of the mapping (u, v).
        Introduces 'nonlinearity' to simulate the breaking of Cauchy-Riemann conditions.
        """
        k = (self.q * V_rf**2) / (4 * self.mass * self.omega_rf**2)

        # Derivatives of u
        ux = 2 * k * x
        uy = -2 * k * y + nonlinearity * (x**2) # Breaking CR with shear

        # Derivatives of v
        vx = 2 * k * y
        vy = 2 * k * x + nonlinearity * (y**2) # Breaking CR

        return np.array([[ux, uy], [vx, vy]])

    def analyze_stability(self, x: float, y: float, V_rf: float, nonlinearity: float = 0.0) -> Dict[str, Any]:
        """
        Analyzes the stability of the trap based on Holomorphic metrics.
        """
        J = self.calculate_jacobian(x, y, V_rf, nonlinearity)
        ux, uy = J[0, 0], J[0, 1]
        vx, vy = J[1, 0], J[1, 1]

        # Cauchy-Riemann Residuals
        cr1 = ux - vy
        cr2 = uy + vx

        # Determinant and Coherence Norm
        det_j = np.linalg.det(J)
        # In the ideal case, J = [[a, -b], [b, a]], so det = a^2 + b^2 = ||v||^2
        coherence_norm = np.sqrt(np.abs(det_j))

        # Shear (Cisalhamento)
        # Defined as the non-conformal part of the deformation
        shear = np.sqrt(cr1**2 + cr2**2)

        # Entropy production Proxy
        entropy_s_y = shear**2

        is_holomorphic = shear < 1e-9

        return {
            "u": float(ux * x / 2 - uy * y / 2), # approx u
            "v": float(vx * x / 2 + vy * y / 2), # approx v
            "jacobian": J.tolist(),
            "det_j": float(det_j),
            "coherence_norm": float(coherence_norm),
            "shear": float(shear),
            "entropy_s_y": float(entropy_s_y),
            "is_holomorphic": bool(is_holomorphic),
            "status": "SAMADHI" if is_holomorphic else "DECOHERENT_SHEAR"
        }

if __name__ == "__main__":
    trap = ConformalPaulTrap()
    print("--- Ideal Holomorphic State ---")
    print(trap.analyze_stability(0.1, 0.1, 100.0, nonlinearity=0.0))

    print("\n--- Decoherent Shear State ---")
    print(trap.analyze_stability(0.1, 0.1, 100.0, nonlinearity=1e5))
