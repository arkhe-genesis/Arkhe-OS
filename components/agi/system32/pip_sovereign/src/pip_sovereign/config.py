#!/usr/bin/env python3
"""
config.py — Sovereign pip configuration
"""
from typing import Dict, Any

class SovereignPipConfig:
    def __init__(self):
        self._config = {}

    @classmethod
    def load(cls) -> "SovereignPipConfig":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return self._config

    def set(self, key: str, value: Any):
        self._config[key] = value

    def save(self):
        pass

def get_config() -> Dict[str, Any]:
    return SovereignPipConfig.load().to_dict()
