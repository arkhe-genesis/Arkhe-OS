import json
import numpy as np
import matplotlib.pyplot as plt
import os

def analyze_thermal_transfer(filepath: str = "/tmp/arkhe/bec_thermal_response.json"):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    with open(filepath) as f:
        data = json.load(f)
    print(f"Thermal Gain h: {data.get('gain_h')}")

if __name__ == "__main__":
    analyze_thermal_transfer()
