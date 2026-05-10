# privacy/parameter_adapter.py — Adaptação dinâmica de parâmetros de privacidade

import logging
from typing import Dict, Any, List

class PrivacyParameterAdapter:
    """
    Adapta ε, security level e outros parâmetros conforme contexto regulatório (FS-74).
    """

    JURISDICTION_RULES = {
        "BR": {"max_epsilon": 0.5, "min_security_bits": 128},
        "EU": {"max_epsilon": 0.3, "min_security_bits": 256},
        "US": {"max_epsilon": 1.0, "min_security_bits": 128}
    }

    def __init__(self, audit_ledger):
        self.audit = audit_ledger

    async def get_parameters_for_context(self, jurisdiction: str, sensitivity: str) -> Dict[str, Any]:
        rule = self.JURISDICTION_RULES.get(jurisdiction, self.JURISDICTION_RULES["US"])

        epsilon = rule["max_epsilon"]
        if sensitivity == "CRITICAL":
            epsilon *= 0.5 # Mais proteção para dados críticos

        params = {
            "jurisdiction": jurisdiction,
            "epsilon": epsilon,
            "security_bits": rule["min_security_bits"],
            "sensitivity": sensitivity
        }

        await self.audit.log_decision(
            decision_type="PRIVACY_PARAMETERS_ADAPTED",
            context=params,
            explainability={"reason": f"Ajuste automático para conformidade com {jurisdiction}"},
            compliance_tags=["dynamic_privacy", "regulatory_adaptation"],
            expected_impact={"benefit": 1.0, "risk": 0.0}
        )

        return params

    def to_dict(self) -> Dict:
        return {
            "status": "active",
            "supported_jurisdictions": list(self.JURISDICTION_RULES.keys())
        }
