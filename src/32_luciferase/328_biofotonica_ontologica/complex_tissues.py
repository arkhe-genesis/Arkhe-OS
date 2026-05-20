"""
Substrato 328: Complex Tissues
Models 3D non-planar photon propagation in complex tissues (Cortex, Myocardium).
"""

class ComplexTissueTopology:
    def __init__(self, tissue_type: str, volume_cm3: float):
        self.tissue_type = tissue_type
        self.volume_cm3 = volume_cm3

        # 3D Scattering factor based on tissue
        if tissue_type == "Cortex":
            self.scattering_factor = 0.85
        elif tissue_type == "Myocardium":
            self.scattering_factor = 0.90
        else:
            self.scattering_factor = 1.0

    def calculate_effective_dose(self, input_photons: int) -> int:
        """
        Reduces the effective photon dose based on 3D scattering.
        """
        return int(input_photons * self.scattering_factor)

    def calculate_phi_c_response(self, effective_photons: int) -> float:
        efficiency = 8.8e-9
        return effective_photons * efficiency
