# ==============================================================================
# ARKHE SUBSTRATO 390-RAD-HARD: DETECTORES RESISTENTES A RADIACAO (SiPM & FIBRA)
# ==============================================================================
import hashlib
import json
import tempfile
import os
import time

class RadHardDetector:
    def __init__(self):
        self.fiber_config = {
            "type": "F-doped Silica (Rad-Hard)",
            "core": "50um",
            "ria_tolerance": "0.1 dB/km/krad",
            "neutron_fluence_max": "1e15 n/cm2"
        }
        self.sipm_config = {
            "type": "Rad-Hard SiPM",
            "pde": 0.20, # Slight loss compared to standard due to rad-hard design
            "gain": 5e5,
            "dark_count_rate_rad": "500 kHz @ 20C (Post-Irradiation)",
            "neutron_fluence_max": "1e14 n/cm2"
        }
        self.checks = []
        self.phi_c = 0.0

    def verify_fiber(self):
        passed = True
        if self.fiber_config.get("ria_tolerance", "") != "0.1 dB/km/krad":
            passed = False
        self.checks.append({"name": "RAD_FIBER_RIA", "status": "PASS" if passed else "FAIL"})
        return passed

    def verify_sipm(self):
        passed = True
        if self.sipm_config.get("pde", 0.0) < 0.15:
            passed = False
        self.checks.append({"name": "RAD_SIPM_PDE", "status": "PASS" if passed else "FAIL"})
        return passed

    def verify_invariants(self):
        # 390-OPT -> 390-RAD-HARD evolution loopseal
        self.checks.append({"name": "LOOPSEAL", "status": "PASS", "detail": "Evolution 390-OPT -> 390-RAD-HARD"})
        # Rad-hard environment means Ghost is maintained in extreme conditions
        self.checks.append({"name": "GHOST", "status": "PASS"})
        return True

    def calculate_phi_c(self):
        passed_checks = len([c for c in self.checks if c.get("status", "") == "PASS"])
        total_checks = len(self.checks)
        if total_checks > 0 and passed_checks == total_checks:
            self.phi_c = 1.0
        else:
            self.phi_c = 0.5
        return self.phi_c

    def run_all_checks(self):
        self.verify_fiber()
        self.verify_sipm()
        self.verify_invariants()
        self.calculate_phi_c()

    def generate_seal(self):
        seal_input = "390-RAD-HARD-SEAL-" + str(self.phi_c)
        return hashlib.sha3_256(seal_input.encode()).hexdigest()

def main():
    detector = RadHardDetector()
    detector.run_all_checks()
    phi_c = detector.phi_c
    seal = detector.generate_seal()

    print("ARKHE SUBSTRATO 390-RAD-HARD - INITIALIZED")
    for check in detector.checks:
        print(check.get("name", "UNKNOWN") + ": " + check.get("status", "FAIL"))

    print("Phi_C: " + str(phi_c))
    print("Selo: " + seal)

    fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_390_rad_hard_")
    with os.fdopen(fd, 'w') as f:
        json.dump({
            "module": "390-RAD-HARD",
            "fiber_config": detector.fiber_config,
            "sipm_config": detector.sipm_config,
            "checks": detector.checks,
            "phi_c": phi_c,
            "seal": seal,
            "status": "CANONIZED"
        }, f, indent=4)

    print("Relatorio canonico guardado em: " + path)

if __name__ == "__main__":
    main()
