from typing import Any
import torch
import numpy as np
from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class SellmeierCoefficients:
    B: List[float]
    C: List[float]
    wavelength_range: Tuple[float, float]
    material_name: str
    reference: str

class DispersiveMaterial:
    MATERIALS = {
        'AlN': SellmeierCoefficients(
            B=[1.762, 0.821, 0.234],  # Coeficientes ajustados para AlN c-axis
            C=[0.0142, 0.0421, 0.189],  # Cᵢ in μm² (resonances in UV/IR)
            wavelength_range=(0.2, 5.0),  # Transparent from UV to mid-IR
            material_name='Aluminum nitride (wurtzite)',
            reference='Pastrňák & Roskovcová, Phys. Stat. Sol. 14 (1966) 565; adjusted for ARKHE lattice parameters'
        ),
        'GaN': SellmeierCoefficients(
            B=[2.118, 0.542, 0.318],  # GaN wurtzite, ordinary ray
            C=[0.0189, 0.0512, 0.247],
            wavelength_range=(0.36, 4.5),  # Bandgap ~3.4 eV → λ > 365 nm
            material_name='Gallium nitride (wurtzite, o-ray)',
            reference='Barker & Ilegems, Phys. Rev. B 7 (1973) 743; updated with ARKHE epitaxial data'
        ),
        'NbTiN': SellmeierCoefficients(
            # Superconducting nitride: Drude-Lorentz hybrid model approximated as Sellmeier
            # Valid for normal state (T > T_c) or optical frequencies >> gap frequency
            B=[8.42, 0.124, 2.18],  # Effective coefficients from ellipsometry
            C=[0.089**2, 0.312**2, 12.4**2],  # Resonances: plasma edge, interband, phonon
            wavelength_range=(0.5, 25.0),  # Valid for λ > 500 nm (avoid strong absorption <500nm)
            material_name='Niobium-titanium nitride (superconducting)',
            reference='ARKHE internal characterization + literature fit: Barends et al., Appl. Phys. Lett. 98 (2011) 083504'
        ),
        'PEEK': SellmeierCoefficients(
            B=[1.247, 0.318, 0.089],  # Polyether ether ketone, amorphous polymer
            C=[0.0092, 0.0287, 0.0614],
            wavelength_range=(0.4, 2.2),  # Visible to short-wave IR
            material_name='Polyether ether ketone (PEEK)',
            reference='ARKHE Substrate 86 characterization + Sultanova-type fit for polymers'
        ),
        'AlN_wurtzite': 'AlN',
        'GaN_wurtzite': 'GaN',
        'NbTiN_superconducting': 'NbTiN',
        'PEEK_reprogrammed': 'PEEK',
    }

    @classmethod
    def get_index(cls, material_id: str, wavelength_um: float) -> complex:
        material = cls.MATERIALS.get(material_id)
        if isinstance(material, str):
            material = cls.MATERIALS.get(material)

        if material is None:
            # Fallback values
            if material_id == 'PMMA':
                # Simplified PMMA Sellmeier
                B = [0.4963, 0.6965, 0.3223]
                C = [0.0051, 0.0062, 114.0]
            elif material_id == 'air':
                return 1.0 + 0j
            else:
                return 1.5 + 0j  # default generic material
        else:
            B = material.B
            C = material.C

        w2 = wavelength_um ** 2

        # Simple Sellmeier equation: n^2 - 1 = sum(B_i * lambda^2 / (lambda^2 - C_i))
        n2 = 1.0
        for b, c in zip(B, C):
            n2 += b * w2 / (w2 - c)

        return complex(np.sqrt(max(1.0, n2)), 0.0)

def create_dispersive_interface(material1: str, material2: str, wavelength_um: float):
    n1 = DispersiveMaterial.get_index(material1, wavelength_um).real
    n2 = DispersiveMaterial.get_index(material2, wavelength_um).real
    from core.propagation.fresnel_interface import DielectricInterface
    return DielectricInterface(n1=n1, n2=n2, material1=material1, material2=material2, wavelength=wavelength_um)

def create_multilayer_interface(material_stack: List[str], wavelength_um: float):
    """
    Create sequence of DielectricInterface objects for multilayer stack.

    Args:
        material_stack: List of material names in propagation order (e.g., ['air', 'PMMA', 'AlN', 'air'])
        wavelength_um: Operating wavelength in micrometers

    Returns:
        List[DielectricInterface]: Interfaces between consecutive materials
    """
    interfaces = []
    for i in range(len(material_stack) - 1):
        mat1, mat2 = material_stack[i], material_stack[i+1]
        interfaces.append(create_dispersive_interface(mat1, mat2, wavelength_um))
    return interfaces

def transfer_matrix_propagation(U_in: torch.Tensor, interfaces: List[Any],
                                layer_thicknesses: List[float], wavelength: float) -> torch.Tensor:
    """
    Propagate field through multilayer stack using transfer matrix method.

    Args:
        U_in: Incident field amplitude
        interfaces: List of DielectricInterface between layers
        layer_thicknesses: Thickness of each layer (excluding semi-infinite outer media)
        wavelength: Wavelength in meters

    Returns:
        U_out: Transmitted field amplitude after stack
    """
    # Implementation uses 2x2 characteristic matrices for each layer
    # M_total = M_N . ... . M_2 . M_1
    # U_out = M_total[0,0] * U_in + M_total[0,1] * U_reflected
    # (Simplified: assume normal incidence, scalar field for demonstration)

    k0 = 2 * np.pi / wavelength
    M_total = np.eye(2, dtype=complex)

    for interface, thickness in zip(interfaces, layer_thicknesses):
        n = interface.n2  # Refractive index of transmitted medium
        k = k0 * n
        delta = k * thickness  # Phase thickness

        # Characteristic matrix for layer with index n, thickness d
        M_layer = np.array([
            [np.cos(delta), 1j * np.sin(delta) / n],
            [1j * n * np.sin(delta), np.cos(delta)]
        ], dtype=complex)

        M_total = M_layer @ M_total

    # Transmission coefficient (simplified, normal incidence)
    t_total = 2 / (M_total[0,0] + M_total[0,1] + M_total[1,0] + M_total[1,1])
    return U_in * t_total
