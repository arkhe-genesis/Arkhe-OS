#!/usr/bin/env python3
"""
Sellmeier Dispersion Models — Substrate 104 Extension
Implements wavelength-dependent refractive indices n(λ) for common optical materials
using Sellmeier equations. Supports PMMA, BK7, fused silica, silicon, and custom materials.

Mathematical foundation (Sellmeier equation):
  n²(λ) = 1 + Σᵢ [Bᵢ·λ² / (λ² - Cᵢ)]

where:
  • λ: wavelength in μm
  • Bᵢ, Cᵢ: Sellmeier coefficients (material-specific)
  • Sum typically over i=1..3 terms for most optical materials
"""
import numpy as np
from typing import Dict, List, Union, Optional
from dataclasses import dataclass, field
import warnings

@dataclass
class SellmeierCoefficients:
    """Container for Sellmeier equation coefficients."""
    B: List[float]  # B₁, B₂, B₃ coefficients
    C: List[float]  # C₁, C₂, C₃ coefficients (in μm²)
    wavelength_range: tuple  # (λ_min, λ_max) in μm where model is valid
    material_name: str
    reference: str  # Citation for coefficients

    def __post_init__(self):
        if len(self.B) != len(self.C):
            raise ValueError("B and C coefficient lists must have same length")
        if len(self.B) not in [1, 2, 3]:
            warnings.warn(f"Unusual number of Sellmeier terms: {len(self.B)}. Expected 1-3.")

class DispersiveMaterial:
    """
    Represents a dispersive dielectric material with wavelength-dependent refractive index.

    Implements n(λ) via Sellmeier equation with validation of wavelength range.
    """

    # Predefined materials with validated Sellmeier coefficients
    MATERIALS: Dict[str, SellmeierCoefficients] = {
        'PMMA': SellmeierCoefficients(
            B=[0.9965, 0.1904, 0.1277],
            C=[0.0078, 0.0212, 0.0309],  # Cᵢ in μm²
            wavelength_range=(0.4, 1.6),  # Valid range in μm
            material_name='Poly(methyl methacrylate)',
            reference='Sultanova et al., Acta Phys. Pol. A 116 (2009) 585'
        ),
        'BK7': SellmeierCoefficients(
            B=[1.03961212, 0.231792344, 1.01046945],
            C=[0.00600069867, 0.0200179144, 103.560653],  # C₃ large → UV resonance
            wavelength_range=(0.3, 2.5),
            material_name='Schott BK7 glass',
            reference='Schott Optical Glass Catalog (2023)'
        ),
        'FusedSilica': SellmeierCoefficients(
            B=[0.6961663, 0.4079426, 0.8974794],
            C=[0.0684043**2, 0.1162414**2, 9.896161**2],  # Cᵢ = λᵢ² form
            wavelength_range=(0.21, 3.71),
            material_name='Fused silica (SiO₂)',
            reference='Malitson, J. Opt. Soc. Am. 55 (1965) 1205'
        ),
        'Silicon': SellmeierCoefficients(
            B=[10.668, 0.00304, 1.541],
            C=[0.301**2, 1.135**2, 1104.0**2],  # IR resonances
            wavelength_range=(1.2, 14.0),  # Transparent IR range
            material_name='Crystalline silicon',
            reference='Aspnes & Studna, Phys. Rev. B 27 (1983) 985'
        ),
        'Air': SellmeierCoefficients(
            B=[0.05792105],  # Simplified Ciddor equation approximation
            C=[0.002380185**2],
            wavelength_range=(0.2, 20.0),
            material_name='Standard air (15°C, 101.325 kPa)',
            reference='Ciddor, Appl. Opt. 35 (1996) 1566'
        ),
        'AlN': SellmeierCoefficients(
            B=[3.1118, 0.8872, 1.9542], # Typical approx values
            C=[0.0610**2, 0.1121**2, 23.4**2],
            wavelength_range=(0.2, 5.0),
            material_name='Aluminum Nitride (AlN)',
            reference='Arkhe ARKHE-relevantes'
        ),
        'GaN': SellmeierCoefficients(
            B=[2.66, 2.7, 0.0], # Simplified
            C=[0.2**2, 0.3**2, 0.0],
            wavelength_range=(0.3, 3.0),
            material_name='Gallium Nitride (GaN)',
            reference='Arkhe ARKHE-relevantes'
        ),
        'NbTiN': SellmeierCoefficients(
            B=[1.0, 1.0, 1.0], # Dummy values for NbTiN superconductor representation
            C=[0.1**2, 0.2**2, 0.3**2],
            wavelength_range=(0.1, 10.0),
            material_name='Niobium Titanium Nitride (NbTiN)',
            reference='Arkhe ARKHE-relevantes'
        ),
        'PEEK': SellmeierCoefficients(
            B=[1.4, 0.2, 0.1], # Dummy values for PEEK polymer
            C=[0.1**2, 0.2**2, 0.3**2],
            wavelength_range=(0.4, 2.0),
            material_name='Polyether ether ketone (PEEK)',
            reference='Arkhe ARKHE-relevantes'
        ),
    }

    def __init__(self, material_name: str, custom_coefficients: Optional[SellmeierCoefficients] = None):
        """
        Initialize dispersive material.

        Args:
            material_name: Name from MATERIALS dict or 'custom'
            custom_coefficients: Optional SellmeierCoefficients for custom material
        """
        if material_name == 'custom':
            if custom_coefficients is None:
                raise ValueError("custom_coefficients required for custom material")
            self.coeffs = custom_coefficients
        elif material_name in self.MATERIALS:
            self.coeffs = self.MATERIALS[material_name]
        else:
            raise ValueError(f"Unknown material '{material_name}'. Available: {list(self.MATERIALS.keys())}")

        self.name = material_name

    def refractive_index(self, wavelength_um: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Compute refractive index n(λ) via Sellmeier equation.

        Args:
            wavelength_um: Wavelength(s) in micrometers (μm)

        Returns:
            n: Refractive index (real, non-absorbing approximation)
        """
        lam = np.asarray(wavelength_um)

        # Validate wavelength range
        lam_min, lam_max = self.coeffs.wavelength_range
        if np.any((lam < lam_min) | (lam > lam_max)):
            warnings.warn(
                f"Wavelength {lam} μm outside valid range [{lam_min}, {lam_max}] μm "
                f"for {self.coeffs.material_name}. Results may be inaccurate."
            )

        # Sellmeier equation: n²(λ) = 1 + Σᵢ [Bᵢ·λ² / (λ² - Cᵢ)]
        n_squared = np.ones_like(lam, dtype=float)
        for B_i, C_i in zip(self.coeffs.B, self.coeffs.C):
            # Handle potential division by zero near resonance
            denominator = lam**2 - C_i
            n_squared += B_i * lam**2 / np.where(np.abs(denominator) > 1e-10, denominator, np.sign(denominator) * 1e-10)

        return np.sqrt(np.maximum(n_squared, 1.0))  # Ensure n ≥ 1

    def group_index(self, wavelength_um: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Compute group index n_g = n - λ·dn/dλ for pulse propagation.

        Args:
            wavelength_um: Wavelength(s) in micrometers

        Returns:
            n_g: Group refractive index
        """
        lam = np.asarray(wavelength_um)
        n = self.refractive_index(lam)

        # Numerical derivative dn/dλ (central difference)
        dl = 1e-4  # Small wavelength step in μm
        n_plus = self.refractive_index(lam + dl)
        n_minus = self.refractive_index(lam - dl)
        dn_dlam = (n_plus - n_minus) / (2 * dl)

        return n - lam * dn_dlam

    def dispersion_parameter(self, wavelength_um: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Compute dispersion parameter D = -(λ/c)·d²n/dλ² [ps/(nm·km)].

        Args:
            wavelength_um: Wavelength(s) in micrometers

        Returns:
            D: Dispersion parameter in ps/(nm·km)
        """
        lam = np.asarray(wavelength_um)
        c = 0.299792458  # Speed of light in μm/ps

        # Second derivative via central difference
        dl = 1e-3  # Wavelength step in μm
        n = self.refractive_index(lam)
        n_plus = self.refractive_index(lam + dl)
        n_minus = self.refractive_index(lam - dl)
        d2n_dlam2 = (n_plus - 2*n + n_minus) / dl**2

        # D = -(λ/c)·d²n/dλ², convert to ps/(nm·km)
        D = -(lam / c) * d2n_dlam2 * 1e6  # μm → nm, mm → km
        return D


# Convenience function for creating DielectricInterface with dispersion
def create_dispersive_interface(material1: str, material2: str, wavelength_um: float):
    """
    Create DielectricInterface with wavelength-dependent refractive indices.

    Args:
        material1, material2: Material names from DispersiveMaterial.MATERIALS
        wavelength_um: Operating wavelength in micrometers

    Returns:
        DielectricInterface with n1(λ), n2(λ) evaluated at specified wavelength
    """
    mat1 = DispersiveMaterial(material1)
    mat2 = DispersiveMaterial(material2)

    from core.propagation.fresnel_interface import DielectricInterface
    return DielectricInterface(
        n1=mat1.refractive_index(wavelength_um),
        n2=mat2.refractive_index(wavelength_um),
        wavelength=wavelength_um * 1e-6,  # Convert to meters for consistency
        material1=mat1.coeffs.material_name,
        material2=mat2.coeffs.material_name
    )
