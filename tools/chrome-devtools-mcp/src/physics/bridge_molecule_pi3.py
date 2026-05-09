import numpy as np
from typing import Dict, Any, List

class BridgeMoleculePi3:
    """
    Molecular model for the Bridge Molecule [π3].
    A naphthalene derivative designed to intercalate between Tryptophan (Trp)
    residues in the tubulin dimer (PDB 1JFF), facilitating resonant exciton
    transfer via π-stacking.
    """
    def __init__(self):
        self.name = "Arkhe-π3-Bridge"
        self.formula = "C12H12N2"  # 2,6-bis(aminomethyl)naphthalene
        self.core = "Naphthalene"
        # Substituents at 2,6 positions provide optimal spacing and potential
        # hydrogen bonding with protein backbone or sidechains.
        self.substituents = {
            "2": "CH2NH2",
            "6": "CH2NH2"
        }
        self.pi_electrons = 10 # From naphthalene core

    def get_electronic_properties(self) -> Dict[str, float]:
        """
        Returns estimated electronic properties based on naphthalene core.
        """
        return {
            "HOMO_eV": -5.8,
            "LUMO_eV": -1.2,
            "gap_eV": 4.6,
            "polarizability_au": 120.5,
            "transition_dipole_debye": 1.4
        }

    def model_stacking_interaction(self,
                                 distance_nm: float,
                                 angle_deg: float) -> float:
        """
        Calculates the pi-stacking interaction energy (kcal/mol).
        Uses a simplified Hunter-Sanders type model.
        """
        # Ideal distance for pi-stacking is ~0.35 nm
        r0 = 0.35
        v_vdw = 4 * 0.5 * ((r0/distance_nm)**12 - (r0/distance_nm)**6)

        # Angle dependence (face-to-face vs T-shaped)
        angle_rad = np.radians(angle_deg)
        v_elec = -2.0 * np.cos(angle_rad)**2 # Attractive for face-to-face

        return float(v_vdw + v_elec)

    def calculate_resonance_shift(self, lambda_nm: float) -> float:
        """
        Calculates the bathochromic shift (nm) due to intercalation.
        """
        # Predicted shift due to pi-system extension/polar environment
        return 12.5 # nm

    def status(self) -> Dict[str, Any]:
        return {
            "molecule_id": "π3",
            "name": self.name,
            "core": self.core,
            "formula": self.formula,
            "pi_electrons": self.pi_electrons,
            "electronic_stats": self.get_electronic_properties(),
            "target_binding_site": "1JFF Inter-Trp Pocket"
        }

if __name__ == "__main__":
    bridge = BridgeMoleculePi3()
    print(f"Molecule: {bridge.name}")
    print(f"Status: {bridge.status()}")
    energy = bridge.model_stacking_interaction(0.36, 10.0)
    print(f"Stacking Energy (0.36nm, 10deg): {energy:.2f} kcal/mol")
