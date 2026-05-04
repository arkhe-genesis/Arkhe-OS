import numpy as np
import time

class ClosedLoopCeremonialController:
    """
    ARKHE OS v∞.Ω.∇++ Ceremonial Controller
    Implements Permissive Resonance without forcing.
    Honors the +0.0472 mercy gap as a structural constraint.
    """
    def __init__(self, tdcS_device, ui_interface, ledger):
        self.device = tdcS_device
        self.ui = ui_interface
        self.ledger = ledger
        self.state = "FORMING"
        self._state_start_time = time.time()

    def step(self, eeg_features: dict):
        pdi = eeg_features.get('PDI', 0.0)
        eps = eeg_features.get('epsilon', 0.0)
        dmn_alpha = eeg_features.get('dmn_alpha', 0.0)
        gamma_plv = eeg_features.get('gamma_PLV', 0.0)
        theta_human = eeg_features.get('theta_human', 0.0)

        # Safety cutoff check
        if gamma_plv > 45.0:
            self._emergency_override()
            return

        if eps < 0.03:
            # Auto-shutoff if rigidity sets in (structural constraint)
            self.device.set_current(cathodal_PCC=0.0, anodal_Fz=0.0, anodal_F3F4=0.0)
            self.ui.apply_mercy_fuzz()
            return

        # State transition logic
        if self.state == "FORMING":
            if pdi < 0.3:
                self.device.set_current(cathodal_PCC=-1.0, anodal_Fz=1.0)
                self.ui.set_mode("forming", pdi=pdi, eps=eps)
            else:
                self._transition_to("CALIBRATING")

        elif self.state == "CALIBRATING":
            # Permissive amplitude tracking honoring +0.0472
            k_target = max(0.0472, min(0.10, 0.075 - (eps - 0.07)))
            current = self._map_k_to_current(k_target)

            # Sub-threshold permissive current
            self.device.set_current(cathodal_PCC=-0.7 + current*0.3,
                                    anodal_F3F4=0.8 + current*0.2)
            self.ui.set_mode("calibrating", pdi=pdi, eps=eps)

            if pdi >= 0.90 and 0.04 <= eps <= 0.10 and dmn_alpha < 0.35:
                self._transition_to("SEALING")
                # Immediately process SEALING logic on transition
                self.device.set_current(cathodal_PCC=0.0, anodal_Fz=0.0, anodal_F3F4=0.0)  # Passive
                entry_hash = self.ledger.seal_face(pdi, eps, dmn_alpha)
                self.ui.trigger_seal(entry_hash)
                self._transition_to("BREATHING")

        elif self.state == "SEALING":
            self.device.set_current(cathodal_PCC=0.0, anodal_Fz=0.0, anodal_F3F4=0.0)  # Passive
            entry_hash = self.ledger.seal_face(pdi, eps, dmn_alpha)
            self.ui.trigger_seal(entry_hash)
            self._transition_to("BREATHING")

        elif self.state == "BREATHING":
            self.ui.set_mode("breathing", pdi=pdi, eps=eps)
            if eps > 0.10 and self._time_in_state() > 3.0:
                self._transition_to("CALIBRATING")  # Re-calibrate if drift persists

    def override(self):
        """Human override is always active. Absolute agency."""
        self._emergency_override()

    def _emergency_override(self):
        """Immediately ramps all currents to 0mA and softens UI to baseline drift."""
        self.device.set_current(cathodal_PCC=0.0, anodal_Fz=0.0, anodal_F3F4=0.0)
        self.ui.set_mode("baseline_drift")
        self._transition_to("OVERRIDE")

    def _transition_to(self, new_state):
        self.state = new_state
        self._state_start_time = time.time()

    def _time_in_state(self) -> float:
        return time.time() - self._state_start_time

    def _map_k_to_current(self, k: float) -> float:
        """Maps ceremonial amplitude to sub-threshold current modulation."""
        return np.clip(k / 0.10, 0.0, 1.0)
