# core/topology/denoising.py
"""
Spatial filtering for experimental n(x,y) fields to improve Q robustness.
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from core.topology.skyrmion_invariant import compute_skyrmion_charge_lattice

def denoise_vector_field(n_field: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """
    Applies Gaussian smoothing to each component, then renormalizes.

    Args:
        n_field: (H, W, 3) vector field
        sigma: Gaussian kernel width in pixels

    Returns:
        Denoised, renormalized vector field
    """
    # Smooth each component independently
    n_smooth = np.stack([
        gaussian_filter(n_field[..., i], sigma=sigma)
        for i in range(3)
    ], axis=-1)

    # Renormalize to unit vectors
    norm = np.linalg.norm(n_smooth, axis=-1, keepdims=True)
    return n_smooth / (norm + 1e-10)

def compute_robust_charge(n_field: np.ndarray, dx: float = 1.0,
                         denoise_sigma: float = 1.0) -> float:
    """
    Computes Q with optional denoising for experimental data.

    Args:
        n_field: Measured or simulated vector field
        dx: Lattice spacing
        denoise_sigma: Gaussian smoothing width (0 = no denoising)

    Returns:
        Topological charge Q
    """
    if denoise_sigma > 0:
        n_field = denoise_vector_field(n_field, sigma=denoise_sigma)
    return compute_skyrmion_charge_lattice(n_field, dx)
