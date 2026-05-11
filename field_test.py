import time
import json
import numpy as np

class FieldTestValidator:
    def __init__(self, port="/dev/ttyUSB0"):
        self.port = port

    def analyze(self, messages):
        return {'avg_gap': 1.5, 'finality_distribution': {}}
