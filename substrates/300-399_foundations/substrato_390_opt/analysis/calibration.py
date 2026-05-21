#!/usr/bin/env python3
"""
ARKHE 390-OPT — calibration.py
Calibração energética do pulso.
"""
import yaml
import os

class EnergyCalibrator:
    def __init__(self, table=None):
        self.table = table or {}

    @classmethod
    def load(cls, path):
        if not os.path.exists(path):
            return cls()
        with open(path, "r") as f:
            return cls(yaml.safe_load(f))

    def calibrate(self, amplitude_raw):
        # placeholder simplificado
        return amplitude_raw * 0.1
