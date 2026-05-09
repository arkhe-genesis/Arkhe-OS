# tests/test_photon_translucency.py

import asyncio
import sys
import os
import logging

sys.path.append(os.getcwd())

from photon_forge import PhotonForge, PhCSpec
from ontological.forge import OntologicalForge
from cathedral_ternary.bitzk import TernaryCircuitBuilder
from dynamic_consent_protocol import DynamicConsentProtocol, PrivacyProfile
from src.arkhe_core.quantum.codex import QuantumCodex
from protocol_forge import ProtocolForge
import pytest

@pytest.mark.asyncio
async def test_photonic_sovereignty_workflow():
    logging.basicConfig(level=logging.INFO)
    print("=== INICIANDO TESTE CATEDRAL TRANSLÚCIDA (FS-87) ===")

    # Setup
    codex = QuantumCodex()
    ternary = TernaryCircuitBuilder()
    consent = DynamicConsentProtocol(explainability_engine=None)

    # Define perfil do cidadão
    citizen_id = "citizen_001"
    consent.set_citizen_profile(
        citizen_id,
        PrivacyProfile.BALANCED,
        {"MedicalDiagnostics": True}
    )

    photon_forge = PhotonForge(codex, ternary, consent)

    # 1. Gera Design de Cristal Fotônico
    print("[PhotonForge] Gerando design de PhC para diagnóstico médico...")
    spec = PhCSpec(
        citizen_id=citizen_id,
        purpose="MedicalDiagnostics",
        target_efficiency=0.99
    )

    design = photon_forge.generate_phc_design(spec)
    print(f"  > Design Hash: {design.design_hash}")
    print(f"  > Prova ZK: {design.coupling_proof[:16]}...")

    # 2. Emite Recibo de Espectro
    print("[PhotonForge] Emitindo recibo para aquisição espectral...")
    spectrum_data = "SPECTRAL_SENSING_DATA_0xAFF23"
    receipt = photon_forge.issue_spectrum_receipt(design.design_hash, spectrum_data)
    print(f"  > Spectrum Hash: {receipt['spectrum_hash']}")
    print(f"  > Status do Recibo: {receipt['status']}")

    # Verificações no Códice
    logs = codex.get_audit_log(limit=5)
    has_design = any(log.get("verdict") == "DESIGN_ANCHORED" for log in logs)
    has_spectrum = any(log.get("verdict") == "SPECTRUM_ISSUED" for log in logs)

    assert has_design is True
    assert has_spectrum is True
    assert ternary.operations_count > 0

    print("=== TESTE CATEDRAL TRANSLÚCIDA CONCLUÍDO COM SUCESSO ===")

if __name__ == "__main__":
    asyncio.run(test_photonic_sovereignty_workflow())
