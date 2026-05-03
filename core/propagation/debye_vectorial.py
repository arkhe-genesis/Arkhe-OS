#!/usr/bin/env python3
"""
Debye Vectorial Propagator — Substrate 104 Extension
"""
import numpy as np
from typing import Tuple, Union, Optional
from core.propagation.fresnel_interface import DielectricInterface

class DebyeVectorialPropagator:
    def __init__(self, NA: float, n_media: float = 1.0):
        self.NA = NA
        self.n_media = n_media
        self.theta_max = np.arcsin(NA / n_media)

    def _polarization_transformation(self, theta: float, psi: float,
                                    interface: Optional[DielectricInterface] = None) -> np.ndarray:
        """
        Compute polarization transformation matrix P(θ,ψ) via Jones calculus.

        Now includes realistic Fresnel transmission coefficients for dielectric interfaces.

        Args:
            theta: Polar angle in lens aperture
            psi: Azimuthal angle
            interface: Optional DielectricInterface for Fresnel coefficients (default: air→air)

        Returns:
            P: 2×2 Jones matrix transforming input polarization to focal plane
        """
        # Rotation to local (s,p) basis
        R_in = np.array([
            [np.cos(psi), np.sin(psi)],
            [-np.sin(psi), np.cos(psi)]
        ], dtype=complex)

        # Fresnel transmission coefficients
        if interface is not None:
            # Compute transmission angle via Snell's law
            theta_t = interface.snell_angle(theta)

            if np.isnan(theta_t):
                # Total internal reflection: no transmission
                t_s, t_p = 0.0, 0.0
            else:
                _, t_s, _, t_p = interface.fresnel_coefficients(theta)
        else:
            # Default: air→air interface (unity transmission)
            t_s, t_p = 1.0, 1.0

        # Diagonal transmission matrix in (s,p) basis
        T = np.array([
            [t_s, 0.0],
            [0.0, t_p]
        ], dtype=complex)

        # Rotation back to lab frame
        R_out = np.array([
            [np.cos(psi), -np.sin(psi)],
            [np.sin(psi), np.cos(psi)]
        ], dtype=complex)

        # Full transformation: lab → (s,p) → Fresnel → (s,p) → lab
        P = R_out @ T @ R_in

        return P
