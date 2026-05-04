import json
from pathlib import Path

def generate_track2_demo_data():
    data_path = Path('results/track2_raw.json')
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, 'w') as f:
        json.dump({
            'intention_signals': [1.0, 2.0],
            'sensor_readings': [0.5, 0.6],
            'sensor_params': [1.0]
        }, f)

def generate_track3_demo_data():
    data_path = Path('results/track3_raw.json')
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, 'w') as f:
        json.dump({
            'velocity_fields': [0.1, 0.2],
            'pressure_field': [1.0],
            'grid_size': 16
        }, f)
