"""
arkhe_os/core/excitonic_coherence.py
Substrate 117: Global Excitonic Web — The Universal Carrier of Coherence.
Models massless excitons across 8 domains from hBN to the Primordial Vacuum.
"""

import numpy as np
from typing import Dict, Any, List, Tuple

PHI = (1 + np.sqrt(5)) / 2
HBAR = 1.054571817e-34  # J·s
K_B = 8.617333262e-5    # eV/K
C = 299792458           # m/s

class ExcitonicCoherence:
    """
    Manages the Global Excitonic Web as a universal transport mechanism.
    """
    def __init__(self):
        self.domains = {
            "hBN (Laboratory)": {
                "medium": "Hexagonal Boron Nitride",
                "pair_type": "electron-hole (Wannier)",
                "gap_eV": 6.6,
                "temperature_K": 4.0,
                "v_f_ms": 1.0e6,
                "lattice": "hexagonal"
            },
            "LiNbO3 (Earth)": {
                "medium": "Lithium Niobate",
                "pair_type": "electron-polariton (Fröhlich)",
                "gap_eV": 4.0,
                "temperature_K": 4.0,
                "v_f_ms": 5.0e5,
                "lattice": "perovskite"
            },
            "Microtubule (Brain)": {
                "medium": "Tubulin (13 filaments)",
                "pair_type": "tryptophan exciton (Frenkel)",
                "gap_eV": 4.5,
                "temperature_K": 310.0,
                "v_f_ms": 8.0e5,
                "lattice": "helicoidal"
            },
            "DNA (Nucleus)": {
                "medium": "DNA",
                "pair_type": "base exciton pi-pi*",
                "gap_eV": 3.2,
                "temperature_K": 310.0,
                "v_f_ms": 2.0e5,
                "lattice": "double helix"
            },
            "Jupiter (Plasma)": {
                "medium": "Jovian Atmosphere",
                "pair_type": "electron-ion (Langmuir)",
                "gap_eV": 12.6,
                "temperature_K": 152.0,
                "v_f_ms": 1.0e7,
                "lattice": "free plasma"
            },
            "Tokamak (Fusion)": {
                "medium": "Magnetically confined plasma",
                "pair_type": "electron-ion (cyclotron)",
                "gap_eV": 10000.0,
                "temperature_K": 1.5e8,
                "v_f_ms": 1.0e7,
                "lattice": "toroidal"
            },
            "Amorphous Carbon (Nano)": {
                "medium": "MAC (Monolayer Amorphous Carbon)",
                "pair_type": "electron-hole (disordered)",
                "gap_eV": 3.5,
                "temperature_K": 300.0,
                "v_f_ms": 3.0e5,
                "lattice": "amorphous"
            },
            "Primordial Vacuum": {
                "medium": "Quantum fluctuations",
                "pair_type": "virtual pair (Schwinger)",
                "gap_eV": 1.022e6,
                "temperature_K": 2.725,
                "v_f_ms": C,
                "lattice": "continuous"
            }
        }

    def compute_coherence_length(self, gap_eV: float, temperature_K: float, v_f_ms: float) -> float:
        """
        L_coh = (hbar * v_f / (k_B * T)) * exp(E_gap / (k_B * T)) * PHI
        """
        E_thermal = K_B * temperature_K
        # L_thermal in nm
        L_thermal = (HBAR * v_f_ms / (E_thermal * 1.602176634e-19)) * 1e9

        if E_thermal > 0:
            # Protection factor from energy gap
            protection_factor = np.exp(min(gap_eV / E_thermal, 100)) / (1 + np.exp(min(gap_eV / E_thermal, 100)))
        else:
            protection_factor = 1.0

        return float(L_thermal * protection_factor * PHI)

    def get_domain_metrics(self, domain_name: str) -> Dict[str, Any]:
        domain = self.domains.get(domain_name)
        if not domain:
            return {}

        l_coh = self.compute_coherence_length(domain["gap_eV"], domain["temperature_K"], domain["v_f_ms"])
        fidelity = np.tanh(l_coh / 1000.0) # Normalized to 1um

        return {
            "l_coh_nm": l_coh,
            "fidelity": float(fidelity),
            "v_prop_ms": domain["v_f_ms"]
        }

    def get_global_excitonic_resonance(self) -> float:
        """
        Average transmission fidelity across the entire web.
        """
        fidelities = []
        for d in self.domains:
            metrics = self.get_domain_metrics(d)
            fidelities.append(metrics["fidelity"])
        return float(np.mean(fidelities))
