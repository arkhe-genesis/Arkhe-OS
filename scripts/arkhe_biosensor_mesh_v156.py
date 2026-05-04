import numpy as np

class ChronoCoilBiosensor:
    def __init__(self, id_name, display_name, unit, noise_level=0.1, squeezing_dB=15):
        self.id_name = id_name
        self.display_name = display_name
        self.unit = unit
        self.noise_level = noise_level
        self.squeezing_dB = squeezing_dB
        self.true_value = None

    def get_reading(self):
        val = self.true_value if self.true_value is not None else np.random.normal(0, 1)
        return {"value": val + np.random.normal(0, self.noise_level)}

class BiosensorMesh:
    def __init__(self):
        self.sensors = {}

    def add_sensor(self, sensor):
        self.sensors[sensor.id_name] = sensor

    def collect_readings(self):
        return {name: sensor.get_reading() for name, sensor in self.sensors.items()}
