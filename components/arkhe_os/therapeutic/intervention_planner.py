class TherapeuticInterventionPlanner:
    def __init__(self):
        self.interventions = {
            "mitochondria_NAD_low": "NAD+ Boosters (e.g., NMN, NR)",
            "cytosol_GSH_low": "NAC (N-acetylcysteine) to boost Glutathione",
            "cytosol_H2O2_high": "Activate Catalase/SOD (Antioxidants)",
            "mitochondria_membrane_potential_low": "Check Complex III / CoQ10 supplementation"
        }

    def evaluate_redox_deviations(self, redox_state: dict, phi_c: float) -> list:
        recommendations = []

        if phi_c >= 0.75:
            return ["Homeostase preservada. Sem intervenções necessárias."]

        if "mitochondria" in redox_state:
            nadh_ratio = redox_state["mitochondria"].get("NADH/NAD+", 0)
            if nadh_ratio < 7: # low
                recommendations.append(self.interventions["mitochondria_NAD_low"])

            delta_psi = redox_state["mitochondria"].get("ΔΨm", 0)
            if delta_psi > -150: # less negative than -150
                recommendations.append(self.interventions["mitochondria_membrane_potential_low"])

        if "cytosol" in redox_state:
            gsh_ratio = redox_state["cytosol"].get("GSH/GSSG", 100)
            if gsh_ratio < 30: # below healthy range 30-100
                recommendations.append(self.interventions["cytosol_GSH_low"])

            h2o2 = redox_state["cytosol"].get("H2O2", 0)
            if h2o2 > 0.1:
                recommendations.append(self.interventions["cytosol_H2O2_high"])

        return recommendations
