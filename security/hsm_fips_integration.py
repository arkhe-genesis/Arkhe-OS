import logging
from typing import Dict, Optional
from security.fips140_3_compliance import FIPS140_3ComplianceChecker, FIPS140_3SecurityLevel

logger = logging.getLogger(__name__)

class HSMProductionPQCSigner:
    """Mock da classe existente com adição da validação FIPS."""

    def __init__(self, config=None, temporal=None):
        self.config = config
        self.temporal = temporal
        if self.config is None:
            class MockConfig:
                provider = "Mock_HSM_Provider"
            self.config = MockConfig()

    async def sign_data(self, data: bytes, context: Optional[Dict] = None) -> Dict:
        """Assinatura mock base."""
        return {"success": True, "signature": b"mock_signature", "fips_compliant": False}

    async def sign_data_fips_compliant(
        self,
        data: bytes,
        context: Optional[Dict] = None
    ) -> Dict:
        """Assina dados com validação FIPS 140-3 prévia."""
        # 1. Validar conformidade FIPS antes de operar
        fips_checker = FIPS140_3ComplianceChecker(
            hsm_provider=self.config.provider,
            target_level=FIPS140_3SecurityLevel.LEVEL_3,
            temporal_chain=self.temporal
        )

        validation = await fips_checker.validate_operation(
            operation_type="pqc_signing",
            hsm_metadata={
                "role_based_auth": True,
                "tamper_response": "zeroize",
                "firmware_selftest": True,
                "rng_algorithm": "CTR_DRBG",
                "side_channel_protections": ["constant_time", "masking"]
            }
        )

        if not validation["compliant"]:
            logger.error(f"❌ Operação bloqueada: não conforme FIPS 140-3")
            return {
                "success": False,
                "error": "fips_compliance_failed",
                "validation_details": validation
            }

        # 2. Prosseguir com assinatura (código existente simulado)
        result = await self.sign_data(data, context)
        result["fips_compliant"] = True
        return result
