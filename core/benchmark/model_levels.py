"""
Five Levels of Wave Propagation Modeling — Substrate 104 Benchmark
Defines hierarchical model complexity for precision/complexity tradeoff analysis.
"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Callable, Dict, List

class ModelLevel(Enum):
    """Hierarchy of wave propagation model complexity."""
    PARAXIAL_FFT = auto()              # Level 1: Scalar FFT, no dispersion, no Fresnel
    DEBYE_SCALAR = auto()              # Level 2: Vectorial Debye, no dispersion, no Fresnel
    DEBYE_FRESNEL = auto()             # Level 3: + Fresnel coefficients (unity n)
    DEBYE_FRESNEL_SELLMEIER = auto()   # Level 4: + wavelength-dependent n(λ)
    DEBYE_FRESNEL_SELLMEIER_TRANSFER = auto()  # Level 5: + multilayer transfer matrix

@dataclass
class ModelBenchmark:
    """Container for benchmark results at each model level."""
    level: ModelLevel
    description: str
    execution_time_ms: float
    memory_usage_mb: float
    chi2_dof: float
    p_value: float
    residual_sigma: float
    material_bias: float  # σ per 0.01 Δn
    spectral_bias: float  # σ per 100 nm Δλ
    overall_accuracy_score: float  # Composite metric [0, 1]

# Model descriptions for documentation
MODEL_DESCRIPTIONS = {
    ModelLevel.PARAXIAL_FFT: "Scalar FFT propagation; paraxial approximation; constant n; air→air interface",
    ModelLevel.DEBYE_SCALAR: "Vectorial Debye integral; high-NA capable; constant n; air→air interface",
    ModelLevel.DEBYE_FRESNEL: "+ Fresnel transmission coefficients; constant n per material",
    ModelLevel.DEBYE_FRESNEL_SELLMEIER: "+ Sellmeier dispersion n(λ) for each material",
    ModelLevel.DEBYE_FRESNEL_SELLMEIER_TRANSFER: "+ Transfer matrix for multilayer dielectric stacks"
}
