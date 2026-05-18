from lean_bridge import LeanToBeaver
from assembly_verifier.smt_reducer import AssemblyVerifier
from redundant_checker.intention_checker import RedundantIntentionChecker

class VitalikProtocolPipeline:
    def __init__(self):
        self.lean = LeanToBeaver()
        self.asm = AssemblyVerifier()
        self.redundant = RedundantIntentionChecker()

    def verify_intent(self, intent: str, lean_spec: str, asm_code: str, implementations: list) -> dict:
        # 1. Lean → BEAVER
        prop = self.lean.convert(lean_spec)
        # 2. Assembly verification
        valid_asm, phi_asm, _ = self.asm.verify(asm_code, prop)
        # 3. Redundant check
        report = self.redundant.check(intent, implementations)
        # 4. Selo final
        overall_phi = (phi_asm + report.phi_c) / 2
        return {"valid": valid_asm and report.matching_seals > 0, "phi_c": overall_phi, "lean_prop": prop, "asm_report": _, "redundant_report": report}
