"""
multi_objective.py — Gerenciador de trade-offs para otimização multi-objetivo
"""

import numpy as np
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto

class ObjectiveDirection(Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    TARGET = "target"

@dataclass
class OptimizationObjective:
    name: str
    direction: ObjectiveDirection
    weight: float
    target_value: Optional[float] = None
    constraint_min: Optional[float] = None
    constraint_max: Optional[float] = None
    priority: int = 0

class MultiObjectiveOptimizer:
    def __init__(self, method="pareto"):
        self.method = method
        self.objectives = {}

    def add_objective(self, name, direction, weight):
        self.objectives[name] = {"direction": direction, "weight": weight}
