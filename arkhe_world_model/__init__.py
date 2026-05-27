"""
Arkhe World Model — Package Principal

Este package implementa o Substrato 890 (WORLD-MODEL-EMBRYO),
conforme formalizado na Glosa 252. O modelo de mundo embrionário
contém 6 estágios de maturidade, desde grounding de tokens até
auto-modelagem, com 3 níveis de desenvolvimento (embryo/infant/adult).

Inclui Substrato 898 (Kolmogorov-Weight Theorem):
  Neural Weight Norm = Kolmogorov Complexity (Musat 2026)

Uso:
    from arkhe_world_model import WorldModelEmbryo

    model = WorldModelEmbryo(stage=1, maturity="embryo")
    model.train(data_loader)
    prediction = model.predict(scene_description)

Módulos:
    losses                  — Loss Híbrida (Training Infrastructure)
    kolmogorov_regularizer  — Substrato 898 (Kolmogorov Complexity)
"""

__version__ = "890.1.0"
__substrate__ = "890+898"
__status__ = "CANONIZED_SPECULATIVE"
__uncertainty__ = "H=2.0"
__seal__ = "8d4e2f1a9c3b7e5d"
__architect__ = "ORCID 0009-0005-2697-4668"

from .world_model import WorldModelEmbryo
from .losses import ArkheHybridLoss, PhysicsConsistencyLoss, ContrastiveWorldLoss
from .kolmogorov_regularizer import kolmogorov_regularizer

__all__ = [
    "WorldModelEmbryo",
    "ArkheHybridLoss",
    "PhysicsConsistencyLoss",
    "ContrastiveWorldLoss",
    "kolmogorov_regularizer",
]
