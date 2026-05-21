import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import math
import unittest
from substrato_377_fractal_time import FractalWaveEngine, AeneidFractalClock, DistributedFractalFFT

class TestSubstrato377(unittest.TestCase):
    def test_fractal_wave_engine(self):
        engine = FractalWaveEngine(node_id=1, position=(0.0, 1.0))
        # Test emission
        wavelet = engine.emit_wavelet(perturbation=1.0, time=1.0)
        self.assertIsInstance(wavelet, float)

        # Test propagation
        engine.add_neighbor(2)
        engine.add_neighbor(3)
        new_state = engine.propagate([0.5, 0.5])
        self.assertGreater(new_state, 0.0)

    def test_aeneid_fractal_clock(self):
        clock = AeneidFractalClock(num_validators=10)
        self.assertEqual(len(clock.validators), 10)

        # Run consensus for 3 steps
        clock.run_fractal_consensus(steps=3, verbose=False)
        for val in clock.validators:
            self.assertIsInstance(val.state, float)

    def test_distributed_fractal_fft(self):
        fft = DistributedFractalFFT(num_nodes=8)
        signal = [math.sin(i) for i in range(8)]
        result = fft.compute_fft(signal)

        self.assertEqual(len(result), 8)
        for r in result:
            self.assertIsInstance(r, float)

if __name__ == '__main__':
    unittest.main()
