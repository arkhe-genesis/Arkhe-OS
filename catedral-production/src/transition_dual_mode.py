# catedral-production/src/transition_dual_mode.py
from enum import Enum

class MigrationPhase(Enum):
    SANDBOX = 0
    SHADOW = 1
    HYBRID = 2
    ACTIVE = 3
    AUTONOMOUS = 4
    FEDERATED = 5
    PLANETARY = 6
    PREPARATION = 7

class TransitionManager:
    def __init__(self):
        self._current_phase = MigrationPhase.SANDBOX

    @property
    def current_phase(self):
        return self._current_phase

    @current_phase.setter
    def current_phase(self, value):
        self._current_phase = value
