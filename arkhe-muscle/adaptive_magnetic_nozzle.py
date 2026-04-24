# adaptive_magnetic_nozzle.py — Bocal magnético controlado por fase óptica

class AdaptiveMagneticNozzle:
    def __init__(self):
        self.expansion_ratio = 1.0

    def set_geometry(self, ratio, divergence):
        print(f"[PAPI] Bocal magnético: ratio={ratio}, divergence={divergence}°")
        self.expansion_ratio = ratio
        return True
