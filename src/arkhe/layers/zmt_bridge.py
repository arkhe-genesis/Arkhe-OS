import numpy as np
from typing import Tuple

try:
    from ..native import zmt_native
except ImportError:
    zmt_native = None

def zero_mode_truncation(left_env: np.ndarray, right_env: np.ndarray,
                         bond_dim: int, kappa: int = 5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply Zero-Mode Truncation to a bond.
    left_env, right_env: (D,D) complex128 tensors representing the contracted environment.
    Returns (U, lambda, V) such that the bond can be updated with reduced dimension (D-1).
    """
    if zmt_native is None:
        raise RuntimeError("zmt_native module not found. Did you compile the C++ extension?")
    return zmt_native.zero_mode_truncation(left_env, right_env, bond_dim, kappa)
