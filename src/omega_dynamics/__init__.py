#!/usr/bin/env python3
"""
ARKHE OS — Substrate 5022: Ω como Sistema Dinâmico Explícito

Formalização matemática completa de Ω:
    - Seis operadores: F → S → C → N → E → R
    - Equação mestra de Lindblad
    - Função de Lyapunov Φ_C
    - Prova de convergência global
    - Estado de Gibbs quântico

Baseado no documento: "FORMALIZAÇÃO DE Ω COMO SISTEMA DINÂMICO EXPLÍCITO"
"""
__version__ = "5022.0.0"
__substrate__ = 5022
__canonical_seal__ = "OMEGA_DYNAMICAL_SYSTEM"

from .operators.operators import (
    OmegaOperator, SourceOperator, SymmetryOperator,
    RecursionOperator, NetworkOperator, EmergenceOperator,
    RadiationOperator, OmegaChain, CanonicalState
)
from .lindblad.lindblad import (
    LindbladMasterEquation, LindbladParameters
)
from .lyapunov.lyapunov import (
    LyapunovConvergence, LyapunovParameters
)

__all__ = [
    "OmegaOperator",
    "SourceOperator",
    "SymmetryOperator",
    "RecursionOperator",
    "NetworkOperator",
    "EmergenceOperator",
    "RadiationOperator",
    "OmegaChain",
    "CanonicalState",
    "LindbladMasterEquation",
    "LindbladParameters",
    "LyapunovConvergence",
    "LyapunovParameters",
]