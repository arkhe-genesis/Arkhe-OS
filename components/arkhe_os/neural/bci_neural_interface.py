import torch
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import hashlib
from abc import ABC, abstractmethod

class BCIProtocol(Enum):
    OPENBCI = auto()
    NEURALINK = auto()
    EMOTIV = auto()
    MUSE = auto()
    SIMULATOR = auto()

class NeuralModality(Enum):
    VISUAL = auto()
    AUDITORY = auto()
    TACTILE = auto()
    MULTIMODAL = auto()

@dataclass
class NeuralStimulationPattern:
    modality: NeuralModality
    frequency_hz: float
    amplitude: float
    modulation: str
    coherence_mapping: Dict[str, float]
    duration_ms: int
    safety_limits: Dict[str, float]

    def validate_safety(self) -> Tuple[bool, Optional[str]]:
        limits = self.safety_limits
        if self.modality == NeuralModality.VISUAL:
            if 15 <= self.frequency_hz <= 25: return False, "Frequência visual 15-25Hz pode induzir fotossensibilidade"
            if self.amplitude > limits.get('visual_max_amplitude', 1.0): return False, "Amplitude visual excede limite"
        return True, None

class BCIHardwareInterface(ABC):
    @abstractmethod
    def connect(self, device_id=None) -> bool: pass
    @abstractmethod
    def disconnect(self): pass
    @abstractmethod
    def send_stimulation(self, pattern) -> bool: pass

class SimulatedBCIInterface(BCIHardwareInterface):
    def connect(self, device_id=None): return True
    def disconnect(self): pass
    def send_stimulation(self, pattern): return True
    def get_device_status(self): return {'connected': True}

class CoherenceToNeuralMapper:
    def __init__(self, default_modality=NeuralModality.VISUAL, safety_profile='conservative'):
        self.default_modality = default_modality
        self.current_profile = {'visual_max_amplitude': 0.6, 'min_inter_stimulus_interval_ms': 2000}
    def phi_c_to_stimulation(self, phi_c, metrics, modality=None, duration_ms=3000):
        modality = modality or self.default_modality
        return NeuralStimulationPattern(modality=modality, frequency_hz=10.0, amplitude=0.5, modulation='none', coherence_mapping={'phi_c': phi_c}, duration_ms=duration_ms, safety_limits=self.current_profile)

class BCINeuralInterface:
    def __init__(self, protocol=BCIProtocol.SIMULATOR, modality=NeuralModality.VISUAL, safety_profile='conservative'):
        self.protocol = protocol
        self.modality = modality
        self.hardware = SimulatedBCIInterface()
        self.mapper = CoherenceToNeuralMapper(default_modality=modality, safety_profile=safety_profile)
        self.connected = False
        self.last_stimulation_time = 0.0

    def connect(self, device_id=None):
        self.connected = self.hardware.connect(device_id)
        return self.connected

    def perceive_coherence(self, phi_c, metrics, condition=None, immediate=True):
        if not self.connected: return {'success': False}
        pattern = self.mapper.phi_c_to_stimulation(phi_c, metrics, self.modality)
        if immediate:
            sent = self.hardware.send_stimulation(pattern)
            return {'success': sent, 'pattern': {'modality': pattern.modality.name, 'frequency_hz': pattern.frequency_hz}}
        return {'success': True, 'pattern_prepared': True}
