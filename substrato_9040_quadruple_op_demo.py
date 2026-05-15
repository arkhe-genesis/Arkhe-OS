#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
substrato_9040_quadruple_op_demo.py — Substrato 9040: Quadruple Operationalization
Demonstração integrada dos 4 componentes: Field Validation, Real-Time Dashboard,
HSM PQC Signing e SIEM Correlation Engine.
"""

import asyncio
import time
import logging
from tests.field.e2e_receiver_validation import FieldE2EValidator, ReceiverConfig, ReceiverType
from security.hsm_pqc_production_signer import HSMProductionSigner, HSMConfig, HSMProvider, PQCSignatureAlgorithm
from integrations.siem_correlation_engine import SIEMCorrelationEngine, AlertSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_demo():
    print("═" * 80)
    print("🏛️ ARKHE Ω‑TEMP v∞.Ω — SUBSTRATO 9040: QUADRUPLE OPERATIONALIZATION")
    print("═" * 80)

    # 1. HSM PQC Signing
    print("\n🔐 1. HSM PQC PRODUCTION SIGNING")
    hsm_config = HSMConfig(
        provider=HSMProvider.THALES_NCRYPT,
        pkcs11_library_path="/opt/nfast/toolkits/pkcs11/libcknfast.so",
        key_label="arkhe-production-key-v1"
    )
    signer = HSMProductionSigner(hsm_config, algorithm=PQCSignatureAlgorithm.DILITHIUM_3)

    # Modo simulado irá rodar se não tiver as bibliotecas
    segment_data = b"MOCK_DASH_SEGMENT_DATA_FOR_ARKHE_BROADCAST"
    metadata = {"segment_id": "seg_001", "channel_id": "ch1"}

    # Chamando manualmente, sem try/except/with para não crashar se falhar em outro lugar
    signing_result = await signer.sign_segment(segment_data, metadata)
    print(f"   ✅ Segmento assinado: {signing_result.signature_hex[:16]}... ({signing_result.signature_size_bytes} bytes)")
    print(f"   ⏱️  Tempo de assinatura: {signing_result.signing_time_ms:.1f}ms")

    # 2. Field E2E Validation
    print("\n🧪 2. FIELD E2E VALIDATION (RECEPTOR REAL)")
    receiver_config = ReceiverConfig(
        receiver_type=ReceiverType.CONSUMER_STB,
        device_id="SONY_XBR_ATSC3_001",
        frequency_mhz=551.25,
        bandwidth_khz=6000,
        modulation="ATSC3"
    )
    validator = FieldE2EValidator(receiver_config)

    # Teste rápido de 2 segundos
    validation_result = await validator.run_field_validation(test_duration_seconds=2, sample_interval_seconds=1.0)
    print(f"   ✅ Validação concluída: Status {validation_result.overall_status.upper()}")
    print(f"   🌀 Φ_C validado em campo: {validation_result.phi_c_value}")
    print(f"   📊 Métricas RF: CNR={validation_result.signal_quality['cnr_db']}dB, MER={validation_result.signal_quality['mer_db']}dB")

    # 3. SIEM Correlation Engine
    print("\n📊 3. SIEM CORRELATION ENGINE")
    siem = SIEMCorrelationEngine()

    # Injetar alertas simulados de múltiplas fontes
    print("   📥 Injetando alertas de diferentes sistemas...")
    await siem.ingest_alert(AlertSource.GATESAIR_MAXIVA, {
        "id": "mx_001", "alert_type": "cnr_low", "severity": "medium",
        "channel_id": "ch1", "cnr_db": 19.5, "message": "CNR below threshold"
    })
    await asyncio.sleep(0.1)

    await siem.ingest_alert(AlertSource.ARKHE_INTERNAL, {
        "id": "ark_001", "alert_type": "phi_c_drop", "severity": "high",
        "channel_id": "ch1", "phi_c_value": 0.94, "message": "Phi_C drop detected"
    })
    await asyncio.sleep(0.5)

    # Verificar alertas correlacionados
    correlated = siem.get_correlated_alerts()
    if correlated:
        c = correlated[0]
        print(f"   ✅ ALERTA CORRELACIONADO GERADO!")
        print(f"   🔴 Regra: {c.correlation_rule} | Severidade: {c.severity.upper()}")
        print(f"   📋 Descrição: {c.description}")
        print(f"   🔧 Ações recomendadas: {', '.join(c.recommended_actions)}")
    else:
        print("   ⚠️ Nenhum alerta correlacionado disparado")

    print("\n📡 4. REAL-TIME Φ_C DASHBOARD")
    print("   O dashboard pode ser executado via: streamlit run monitoring/phi_c_broadcast_dashboard.py")

    print("\n✅ QUADRUPLE OPERATIONALIZATION DEMO COMPLETA")

if __name__ == "__main__":
    asyncio.run(run_demo())
