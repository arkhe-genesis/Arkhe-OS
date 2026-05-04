#!/usr/bin/env python3
"""
Fresnel Coefficients for Dielectric Interfaces — Substrate 104 Extension
Implements realistic transmission/reflection coefficients for s- and p-polarized light
at dielectric interfaces (e.g., air/PMMA, air/substrate, immersion oil/glass).

Mathematical foundation (Fresnel equations):
  r_s = (n1·cosθ_i - n2·cosθ_t) / (n1·cosθ_i + n2·cosθ_t)
  t_s = 2·n1·cosθ_i / (n1·cosθ_i + n2·cosθ_t)
  r_p = (n2·cosθ_i - n1·cosθ_t) / (n2·cosθ_i + n1·cosθ_t)
  t_p = 2·n1·cosθ_i / (n2·cosθ_i + n1·cosθ_t)

where:
  • n1, n2: refractive indices of incident/transmitted media
  • θ_i: angle of incidence
  • θ_t: angle of transmission (Snell's law: n1·sinθ_i = n2·sinθ_t)
"""
import numpy as np
from typing import Tuple, Union, Optional
from dataclasses import dataclass
import warnings

@dataclass
class DielectricInterface:
    """Represents a planar interface between two dielectric media."""
    n1: float  # Refractive index of incident medium
    n2: float  # Refractive index of transmitted medium
    wavelength: Optional[float] = None  # Optional: for dispersive materials
    material1: str = "air"  # Optional: for documentation
    material2: str = "unknown"

    # Sellmeier coefficients dictionary for common materials
    # Form: { material_name: [(B1, C1), (B2, C2), (B3, C3)] }
    # where n^2(lambda) = 1 + sum( B_i * lambda^2 / (lambda^2 - C_i) )
    # lambda is expected in micrometers (um)
    SELLMEIER_COEFFS = {
        'PMMA': [
            (0.99654, 0.00787),
            (0.18964, 0.02191),
            (0.00411, 3.85727)
        ],
        'BK7 glass': [
            (1.03961212, 0.00600069867),
            (0.231792344, 0.0200179144),
            (1.01046945, 103.560653)
        ],
        'Si @ 1550nm': [ # Note: silicon is typically computed differently, but we approximate for the common form if possible or override. We will provide a simple approximation for demo.
            # Using common Sellmeier for intrinsic silicon
            (10.6684293, 0.0909122),
            (0.0030434748, 1.287660),
            (1.54133408, 1e6) # large value
        ]
    }

    def _compute_refractive_index(self, material: str, default_n: float) -> float:
        if self.wavelength is None:
            return default_n

        # Convert wavelength to um if it's very large/small (assume nm if > 100 or m if < 1e-4)
        wl_um = self.wavelength
        if wl_um > 100:
            wl_um /= 1000.0 # nm to um
        elif wl_um < 1e-4:
            wl_um *= 1e6 # m to um

        if material in self.SELLMEIER_COEFFS:
            coeffs = self.SELLMEIER_COEFFS[material]
            n_sq = 1.0
            wl_sq = wl_um**2
            for B, C in coeffs:
                n_sq += (B * wl_sq) / (wl_sq - C)
            return np.sqrt(n_sq)

        return default_n

    def __post_init__(self):
        if self.wavelength is not None:
            self.n1 = self._compute_refractive_index(self.material1, self.n1)
            self.n2 = self._compute_refractive_index(self.material2, self.n2)

        if self.n1 <= 0 or self.n2 <= 0:
            raise ValueError("Refractive indices must be positive")

    def snell_angle(self, theta_incident: Union[float, np.ndarray]) -> np.ndarray:
        """
        Compute transmission angle via Snell's law.
        Returns NaN for total internal reflection.
        """
        sin_theta_t = (self.n1 / self.n2) * np.sin(theta_incident)
        # Handle total internal reflection properly without invalid value warning
        safe_sin_theta_t = np.clip(sin_theta_t, -1.0, 1.0)
        theta_t = np.where(
            np.abs(sin_theta_t) <= 1.0,
            np.arcsin(safe_sin_theta_t),
            np.nan
        )
        return theta_t

    def fresnel_coefficients(self, theta_incident: Union[float, np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute Fresnel reflection/transmission coefficients for s- and p-polarization.

        Returns:
            r_s, t_s, r_p, t_p: Complex coefficients (amplitude, not intensity)
        """
        theta_i = np.asarray(theta_incident)
        theta_t = self.snell_angle(theta_i)

        # Handle total internal reflection: coefficients become complex with |r|=1
        tir_mask = np.isnan(theta_t)

        # Precompute trigonometric terms
        cos_i = np.cos(theta_i)
        # Avoid invalid value encountered in sqrt by taking abs or masking properly
        val_under_sqrt = (self.n1/self.n2)**2 * np.sin(theta_i)**2 - 1
        safe_val_under_sqrt = np.where(val_under_sqrt > 0, val_under_sqrt, 0)
        cos_t = np.where(tir_mask, 1j * np.sqrt(safe_val_under_sqrt), np.cos(np.where(tir_mask, 0, theta_t)))

        # s-polarization (TE): electric field perpendicular to plane of incidence
        denom_s = self.n1 * cos_i + self.n2 * cos_t
        r_s = np.where(tir_mask,
                      (self.n1 * cos_i - self.n2 * cos_t) / denom_s,  # Complex for TIR
                      (self.n1 * cos_i - self.n2 * cos_t) / denom_s)
        t_s = np.where(tir_mask,
                      2 * self.n1 * cos_i / denom_s,
                      2 * self.n1 * cos_i / denom_s)

        # p-polarization (TM): electric field parallel to plane of incidence
        denom_p = self.n2 * cos_i + self.n1 * cos_t
        r_p = np.where(tir_mask,
                      (self.n2 * cos_i - self.n1 * cos_t) / denom_p,
                      (self.n2 * cos_i - self.n1 * cos_t) / denom_p)
        t_p = np.where(tir_mask,
                      2 * self.n1 * cos_i / denom_p,
                      2 * self.n1 * cos_i / denom_p)

        return r_s, t_s, r_p, t_p

    def reflectance_transmittance(self, theta_incident: Union[float, np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute intensity reflectance R and transmittance T (power coefficients).

        Returns:
            R_s, T_s, R_p, T_p: Real values in [0, 1] satisfying R + T = 1 (no absorption)
        """
        r_s, t_s, r_p, t_p = self.fresnel_coefficients(theta_incident)

        # Reflectance: R = |r|²
        R_s = np.abs(r_s)**2
        R_p = np.abs(r_p)**2

        # Transmittance: T = (n2·cosθ_t)/(n1·cosθ_i) · |t|² (energy conservation)
        theta_t = self.snell_angle(theta_incident)
        cos_i = np.cos(theta_incident)
        cos_t = np.where(np.isnan(theta_t), 0, np.cos(theta_t))  # T=0 for TIR

        # Avoid division by zero at grazing incidence
        with np.errstate(divide='ignore', invalid='ignore'):
            T_s = np.where(
                (cos_i > 1e-10) & (~np.isnan(theta_t)),
                (self.n2 * cos_t) / (self.n1 * cos_i) * np.abs(t_s)**2,
                0.0
            )
            T_p = np.where(
                (cos_i > 1e-10) & (~np.isnan(theta_t)),
                (self.n2 * cos_t) / (self.n1 * cos_i) * np.abs(t_p)**2,
                0.0
            )

        return R_s, T_s, R_p, T_p

    def brewster_angle(self) -> Optional[float]:
        """Compute Brewster angle for p-polarization (R_p = 0). Returns None if no solution."""
        if self.n2 > self.n1:
            return float(np.arctan(self.n2 / self.n1))
        return None

    def critical_angle(self) -> Optional[float]:
        """Compute critical angle for total internal reflection. Returns None if n2 >= n1."""
        if self.n1 > self.n2:
            return float(np.arcsin(self.n2 / self.n1))
        return None

# Predefined common interfaces for Substrate 104 validation
INTERFACES = {
    'air_pmma': DielectricInterface(n1=1.0003, n2=1.49, material1='air', material2='PMMA'),
    'air_glass': DielectricInterface(n1=1.0003, n2=1.52, material1='air', material2='BK7 glass'),
    'air_silicon': DielectricInterface(n1=1.0003, n2=3.48, material1='air', material2='Si @ 1550nm'),
    'oil_glass': DielectricInterface(n1=1.515, n2=1.52, material1='immersion oil', material2='BK7 glass'),
    'pmma_air': DielectricInterface(n1=1.49, n2=1.0003, material1='PMMA', material2='air'),  # Reverse
}
