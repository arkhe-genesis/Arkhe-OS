#!/usr/bin/env python3
"""
ARKHE 390-OPT — pulse_classifier.py
Algoritmo de detecção e classificação de partículas baseado em forma de pulso.
"""

class PulseClassifier:
    def __init__(self, threshold_sigma=5.0, coincidence_window_ns=100):
        self.threshold_sigma = threshold_sigma
        self.coincidence_window_ns = coincidence_window_ns
        self._recent_events = []
        self._baseline = 0.0
        self._baseline_std = 1.0

    def process(self, event: dict) -> dict:
        self._update_baseline(event["amplitude_raw"])

        threshold = self._baseline + self.threshold_sigma * self._baseline_std
        detected = event["amplitude_raw"] > threshold

        result = {"detected": False, "particle_type": "none", "event": event}

        if detected:
            self._recent_events.append(event["timestamp_ns"])
            self._prune_old_events()

            # Classificação por forma de pulso
            width_ns = self._estimate_width(event)
            if width_ns < 10:
                result["particle_type"] = "alpha"
            elif width_ns < 50:
                result["particle_type"] = "beta_gamma"
            else:
                result["particle_type"] = "muon"

            result["detected"] = True

        return result

    def _update_baseline(self, amplitude):
        # Moving average + std calculation (simplified)
        self._baseline = 0.99 * self._baseline + 0.01 * amplitude
        self._baseline_std = max(1.0, 0.99 * self._baseline_std + 0.01 * abs(self._baseline - self._baseline_std))

    def _prune_old_events(self):
        cutoff = self._recent_events[-1] - self.coincidence_window_ns
        self._recent_events = [t for t in self._recent_events if t > cutoff]

    def _estimate_width(self, event):
        # Placeholder: width estimation from pulse shape analysis
        # In production: use ADC samples to calculate FWHM
        return 15.0 if "alpha" in str(event.get("flags", "")) else 25.0
