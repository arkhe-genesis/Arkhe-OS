# simulation.py
import numpy as np
from .interferometer import FisherInterferometer
from .wave_generator import WaveGenerator
from .controllers import PIDDamper, LQRDamper

class CathedralSimulation:
    def __init__(self, duration=100.0, dt=0.1, controller_type='lqr', **controller_kwargs):
        self.duration = duration
        self.dt = dt
        self.n_steps = int(duration / dt)
        self.times = np.linspace(0, duration, self.n_steps)
        self.interf = FisherInterferometer()
        self.wave_gen = WaveGenerator(seed=42)
        if controller_type.lower() == 'pid':
            self.controller = PIDDamper(**controller_kwargs)
        elif controller_type.lower() == 'lqr':
            self.controller = LQRDamper(**controller_kwargs)
        else:
            self.controller = None
        self.phases_open = []
        self.phases_closed = []
        self.controls = []

    def run(self):
        for t in self.times:
            h_open = self.wave_gen.strain(t)
            self.phases_open.append(self.interf.measure(h_open))
            if self.controller is not None:
                h_meas = self.wave_gen.strain(t)
                phase_meas = self.interf.measure(h_meas)
                u = self.controller.update(phase_meas, self.dt)
                self.controls.append(u)
                attenuation = 1.0 / (1.0 + 0.1 * np.abs(u))
                self.wave_gen.set_amplitude_factor(attenuation)
                h_closed = self.wave_gen.strain(t)
                self.phases_closed.append(self.interf.measure(h_closed))
            else:
                self.phases_closed.append(self.phases_open[-1])
        return self.times, self.phases_open, self.phases_closed, self.controls
