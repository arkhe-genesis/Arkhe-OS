import unittest
from arkhe_os.layers.energy.microsparc import MicroSPARC, MicroSPARCArray

class TestMicroSPARC(unittest.TestCase):
    def test_single_chip_output(self):
        chip = MicroSPARC("test1")
        out = chip.step(1.0)
        self.assertGreater(out['voltage'], 0)
        self.assertAlmostEqual(out['current_ua'], 25, delta=10)
        self.assertLess(out['power_uw'], 200)

    def test_array_series(self):
        array = MicroSPARCArray(10, series=True)
        out = array.step(1.0)
        # 10 chips em série devem somar tensão ~15V
        self.assertAlmostEqual(out['voltage'], 15, delta=6)

    def test_temporal_anchor(self):
        chip = MicroSPARC("test2")
        # Forçar passagem de 3600 segundos
        chip._uptime_s = 3599
        out = chip.step(2)  # agora >= 3600
        self.assertIsNotNone(chip.temporal_anchor)

if __name__ == "__main__":
    unittest.main()
