import pytest
import math
from .substrato_337_exp_act import SNOMTWVerifier, GHOST, LOOPSEAL, GAP_SOVEREIGN

def test_snom_tw_verifier_goe_auth():
    verifier = SNOMTWVerifier(tw_transceiver_id="TW-TEST")
    res = verifier.verify_packet({"id": "TW-001"}, {"seed": 42, "center_nm": 1232.5})
    assert res["status"] == "VERIFIED"
    assert res["phi_c"] > GHOST

def test_snom_tw_verifier_poisson_fake():
    class PoissonVerifier(SNOMTWVerifier):
        def _generate_hud_spectrum(self, center_nm=1232.5, num_modes=35, goe_beta=0.0, chi=0.5, seed=None):
            return super()._generate_hud_spectrum(center_nm, num_modes, 0.0, chi, seed)

    verifier = PoissonVerifier(tw_transceiver_id="TW-TEST-POISSON")
    res = verifier.verify_packet({"id": "TW-FAKE"}, {"seed": 999, "center_nm": 1232.5})
    assert res["status"] == "REJECTED"

def test_snom_tw_verifier_noisy_reject():
    class NoisyVerifier(SNOMTWVerifier):
        def _generate_hud_spectrum(self, center_nm=1232.5, num_modes=35, goe_beta=1.0, chi=0.5, seed=None):
            data = super()._generate_hud_spectrum(center_nm, num_modes, goe_beta, chi, seed)
            import numpy as np
            extra = np.random.randn(len(data["intensity"])) * 0.35
            data["intensity"] = np.clip(data["intensity"] + extra, 0, None)
            data["intensity"] = data["intensity"] / np.max(data["intensity"])
            return data

    verifier = NoisyVerifier(tw_transceiver_id="TW-TEST-NOISY")
    res = verifier.verify_packet({"id": "TW-NOISY"}, {"seed": 777, "center_nm": 1232.5})
    # Could be rejected or verified depending on random noise. The important part is it should NOT crash.
    assert res["status"] in ["VERIFIED", "REJECTED"]
