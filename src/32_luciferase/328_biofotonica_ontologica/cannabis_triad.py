"""
Substrato 328-CANNABIS: Triade Fotônica Canônica
1. Cannabis Biophoton Reporter
2. Cannabinoid Biosensor (KM206)
3. Photodynamic Cannabinoid Therapy (PDT-C)
"""
import math

class CannabisBiophotonReporter:
    def __init__(self, initial_phic=0.500294):
        self.phic = initial_phic
        self.events = []
        self.thc_level = 0.0
        self.cbd_level = 0.0
        self.cbg_level = 0.0

        self.GHOST = math.sqrt(3)/3.0
        self.EFFICIENCY = 8.8e-9

    def report_expression(self, promoter: str, activity: float, photons: int):
        # THC/CBD/CBG increases dynamically based on activity
        if promoter == "THC_synthase_promoter":
            self.thc_level += activity * 0.01
        elif promoter == "CBD_synthase_promoter":
            self.cbd_level += activity * 0.01
        elif promoter == "CBG_synthase_promoter":
            self.cbg_level += activity * 0.01

        self.events.append({
            "promoter": promoter,
            "activity": activity,
            "photons": photons
        })

        # Calculate phic impact
        self.phic += photons * self.EFFICIENCY

    def is_ghost_preserved(self):
        return self.phic >= self.GHOST

class CannabinoidBiosensorKM206:
    def __init__(self):
        self.limit_pm = 100.0
        self.phic = 0.780000

        self.synthetic_signatures = {
            "JWH-018": lambda conc: conc > 300,
            "AM-2201": lambda conc: conc > 400,
            "5F-ADB": lambda conc: conc > 50
        }

    def detect_sample(self, sample_id: str, thc_conc_pm: float, scras: list = None):
        if scras is None:
            scras = []

        detected = thc_conc_pm >= self.limit_pm

        critical_risk = False
        detected_scras = []

        for scra in scras:
            if scra in self.synthetic_signatures and self.synthetic_signatures[scra](thc_conc_pm):
                critical_risk = True
                detected_scras.append(scra)

        # Any synthetic presence above threshold marks critical risk
        if detected_scras:
            critical_risk = True

        risk = "CRITICAL" if critical_risk else ("POSITIVE" if detected else "NEGATIVE")

        return {
            "sample_id": sample_id,
            "detected": detected,
            "risk": risk,
            "scras": detected_scras
        }

class PhotodynamicCannabinoidTherapy:
    def __init__(self):
        self.phic = 0.717823

    def apply_session(self, tumor_id: str, cbd_ug: float, ir_dose: float, volume_mm3: float):
        # Efficacy model loosely based on combination of IR and CBD
        efficacy_base = (ir_dose * cbd_ug) / (volume_mm3 * 10.0)
        efficacy_pct = min(100.0, max(0.0, efficacy_base * 100))

        # Total damage calculated
        total_damage = (ir_dose * cbd_ug) / 200.0

        return {
            "tumor_id": tumor_id,
            "efficacy_pct": efficacy_pct,
            "total_damage": total_damage
        }
