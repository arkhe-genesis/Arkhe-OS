"""
Substrato 328: Pre-Clinical Protocol
Models ethical animal tissue responses and CEUA adaptation.
"""
from typing import Dict

class PreClinicalProtocol:
    def __init__(self, ceua_approval: str):
        self.ceua_approval = ceua_approval
        self.subjects = {}

    def enroll_subject(self, subject_id: str, tissue_type: str, initial_phic: float):
        self.subjects[subject_id] = {
            "tissue": tissue_type,
            "phic": initial_phic,
            "status": "ENROLLED"
        }

    def apply_therapy(self, subject_id: str, dose_photons: int) -> Dict:
        if subject_id not in self.subjects:
            raise ValueError(f"Subject {subject_id} not found.")

        subject = self.subjects[subject_id]

        # In pre-clinical complex tissues, efficiency might vary slightly.
        # We use canonical 8.8e-9 as baseline
        efficiency = 8.8e-9

        if subject["tissue"] == "Cortex":
            efficiency *= 0.95 # Slight absorption
        elif subject["tissue"] == "Myocardium":
            efficiency *= 0.98

        delta_phic = dose_photons * efficiency
        subject["phic"] += delta_phic
        subject["status"] = "TREATED"

        return subject
