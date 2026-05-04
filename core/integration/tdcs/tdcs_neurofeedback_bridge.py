import time
from typing import Dict, Any

class TDCSNeurofeedbackBridge:
    """Bridge to map ledger state transitions to tDCS/Neurofeedback hardware protocols."""

    def __init__(self):
        self.connected = False
        self.current_state = "IDLE"
        self.intensity_ma = 0.0

    def connect(self):
        """Mock hardware connection."""
        self.connected = True
        print("[tDCS] Hardware Connected.")

    def apply_stimulation(self, state: str, k: float, pdi: float, epsilon: float) -> Dict[str, Any]:
        """Map ledger state and calibration metrics to stimulation parameters."""
        if not self.connected:
            return {"status": "error", "message": "tDCS hardware not connected."}

        self.current_state = state
        response = {"state": state, "timestamp": time.time()}

        if state == "FORMING":
            self.intensity_ma = 0.5  # Baseline
            response["action"] = "BASELINE_STIM"
            response["intensity"] = self.intensity_ma
            response["target_region"] = "F3/F4" # DLPFC

        elif state == "CALIBRATING":
            # Map k (ceremonial amplitude 0.0472 - 0.10) to tDCS intensity
            # E.g., intensity between 1.0mA and 2.0mA
            normalized_k = (k - 0.0472) / (0.10 - 0.0472) if k >= 0.0472 else 0.0
            normalized_k = max(0.0, min(1.0, normalized_k))

            self.intensity_ma = 1.0 + (normalized_k * 1.0)

            # Map epsilon (mercy gap 0.04 - 0.10) to stimulation frequency/type if using tACS
            # For tDCS, we hold steady but modulate based on drift.
            if epsilon > 0.10:
                 response["action"] = "DRIFT_CORRECTION"
                 self.intensity_ma *= 0.9 # Reduce slightly if drifting
            elif epsilon < 0.04:
                 response["action"] = "RIGIDITY_OPENING"
                 self.intensity_ma *= 1.1 # Increase slightly if too tight
            else:
                 response["action"] = "HOLD_STEADY"

            response["intensity"] = self.intensity_ma
            response["target_region"] = "Pz/Cz" # DMN targeting

        elif state == "SEALED":
            # Fade out stimulation over 5 seconds (mock)
            self.intensity_ma = 0.0
            response["action"] = "FADE_OUT"
            response["intensity"] = self.intensity_ma
            response["target_region"] = "ALL"
            response["message"] = "Protocol complete. Scaffold dropped."

        else:
            response["action"] = "UNKNOWN_STATE"

        # print(f"[tDCS] State: {state} | Action: {response['action']} | Intensity: {self.intensity_ma:.2f}mA")
        return response

    def disconnect(self):
        """Mock hardware disconnection."""
        self.intensity_ma = 0.0
        self.connected = False
        print("[tDCS] Hardware Disconnected.")
