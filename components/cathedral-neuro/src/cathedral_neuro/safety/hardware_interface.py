"""
hardware_interface.py — Interface com hardware robótico
"""

import asyncio
import time
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass

@dataclass
class RoboticArmState:
    position: List[float]
    velocity: List[float]
    force: List[float]
    timestamp: float
    emergency_brake_engaged: bool = False

class RoboticHardwareInterface:
    def __init__(self, device_config):
        self.config = device_config
        self._connected = False

    async def connect(self):
        self._connected = True
        return True

    async def emergency_brake(self, force=100.0, feedback_intensity=0.5):
        pass

    async def send_tactile_feedback(self, pattern, intensity):
        pass
