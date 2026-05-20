#!/usr/bin/env python3
import asyncio
import pytest
from unittest.mock import patch, MagicMock
from tests.field.e2e_receiver_validation import FieldE2EValidator, ReceiverConfig, ReceiverType
from security.hsm_pqc_production_signer import HSMProductionSigner, HSMConfig, HSMProvider, PQCSignatureAlgorithm, HSM_AVAILABLE
from integrations.siem_correlation_engine import SIEMCorrelationEngine, AlertSource

def test_receiver_validation():
    async def run():
        config = ReceiverConfig(
            receiver_type=ReceiverType.CONSUMER_STB,
            device_id="test",
            frequency_mhz=500.0,
            bandwidth_khz=6000,
            modulation="ATSC3"
        )
        val = FieldE2EValidator(config)
        res = await val.run_field_validation(1, 0.5)
        assert res.overall_status == "passed"
    asyncio.run(run())

@pytest.mark.skipif(not HSM_AVAILABLE, reason="HSM environment not available")
def test_hsm_signer():
    async def run():
        hsm_config = HSMConfig(
            provider=HSMProvider.THALES_NCRYPT,
            pkcs11_library_path="mock",
            key_label="arkhe-production-key-v1"
        )
        signer = HSMProductionSigner(hsm_config, algorithm=PQCSignatureAlgorithm.DILITHIUM_3)
        res = await signer.sign_segment(b"test", {})
        assert res.success is True
    asyncio.run(run())

def test_signature_size_mapping_mock():
    """Testa o mapeamento sig_size_estimate sem HSM fisico."""
    async def run():
        hsm_config = HSMConfig(
            provider=HSMProvider.THALES_NCRYPT,
            pkcs11_library_path="mock",
            key_label="arkhe-production-key-v1"
        )
        with patch('security.hsm_pqc_production_signer.HSM_AVAILABLE', True), \
             patch('security.hsm_pqc_production_signer.PQC_AVAILABLE', True):
            signer = HSMProductionSigner(hsm_config, algorithm=PQCSignatureAlgorithm.HAWK)
            signer._hsm_session = MagicMock()
            with patch.object(signer, '_sign_with_hsm', return_value=b'\x00' * 555):
                res = await signer.sign_segment(b"test", {})
                assert res.success is True
                assert res.signature_size_bytes == 555
                assert res.algorithm == "HAWK"
    asyncio.run(run())

def test_siem():
    async def run():
        siem = SIEMCorrelationEngine()
        await siem.ingest_alert(AlertSource.GATESAIR_MAXIVA, {
            "id": "mx_001", "alert_type": "cnr_low", "severity": "medium",
            "channel_id": "ch1", "cnr_db": 19.5, "message": "CNR below threshold"
        })
        await siem.ingest_alert(AlertSource.ARKHE_INTERNAL, {
            "id": "ark_001", "alert_type": "phi_c_drop", "severity": "high",
            "channel_id": "ch1", "phi_c_value": 0.94, "message": "Phi_C drop detected"
        })
        await asyncio.sleep(0.5)
        corr = siem.get_correlated_alerts()
        assert len(corr) > 0
    asyncio.run(run())
