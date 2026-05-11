# catedral-production/src/cathedral_organism/state.py
from enum import Enum, auto

class OrganismState(Enum):
    INITIALIZING = auto()
    RUNNING = auto()
    SHUTTING_DOWN = auto()
    STOPPED = auto()
    DEAD = auto()
    RECOVERING = auto()

class StateTransition:
    pass
