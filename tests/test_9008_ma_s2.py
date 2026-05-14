#!/usr/bin/env python3
"""
Suíte de Testes MA‑S2 – Substrato 9008
Valida os 4 domínios de conformidade: CVS, APM, INV, ARO
"""

import sys
import os
import hashlib
import asyncio
import time
import json
import importlib.util

# Adiciona raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arkhe.security import ThreatDatabase, GuardianAttractor, Finding, AttackPath
from arkhe.chain import TemporalChain, Inventory
from arkhe.orchestrator import FleetOrchestrator

spec = importlib.util.spec_from_file_location("ma_s2_engine", os.path.join(os.path.dirname(__file__), "..", "substrates", "9008_ma_s2", "ma_s2_engine.py"))
ma_s2_engine = importlib.util.module_from_spec(spec)
sys.modules["ma_s2_engine"] = ma_s2_engine
spec.loader.exec_module(ma_s2_engine)

MA_S2_Engine = ma_s2_engine.MA_S2_Engine
MA_S2_Report = ma_s2_engine.MA_S2_Report

# ═════════════════════════════════════════════════════════════
# 1. TESTES CVS – Continuous Vulnerability Scanning
# ═════════════════════════════════════════════════════════════

def test_cvs_01_scan_artifact():
    """CVS‑0.1: Guardian escaneia artefato e retorna findings."""
    db = ThreatDatabase()
    guardian = GuardianAttractor(db)

    artifact = "arkhe-runtime-v8.0.0-3"
    findings = asyncio.run(guardian.scan_artifact(artifact))

    assert isinstance(findings, list)
    assert len(findings) > 0, "Deve encontrar pelo menos 1 vulnerabilidade"
    for f in findings:
        assert isinstance(f, Finding)
        assert f.cve.startswith("CVE-")
    print(f"   ✅ CVS‑0.1: {len(findings)} findings para {artifact}")

def test_cvs_02_epss_kev_enrichment():
    """CVS‑0.2: EPSS + KEV enrichment automático."""
    db = ThreatDatabase()
    f = Finding(cve="CVE-2026-12345", cvss_score=9.8)
    db.enrich_finding(f)

    assert f.epss_score == 0.95, f"EPSS deve ser 0.95, got {f.epss_score}"
    assert f.kev_listed is True, "KEV deve estar listado"
    assert f.compute_ma_s2_severity() >= 0.8, "Severidade MA‑S2 deve ser crítica"
    print(f"   ✅ CVS‑0.2: EPSS={f.epss_score}, KEV={f.kev_listed}, Severity={f.compute_ma_s2_severity():.4f}")

def test_cvs_04_auto_escalation():
    """CVS‑0.4: Escalada automática para findings críticos."""
    temporal = TemporalChain()
    db = ThreatDatabase()
    guardian = GuardianAttractor(db)
    orchestrator = FleetOrchestrator(temporal)

    f = Finding(cve="CVE-2026-00001", cvss_score=10.0)
    db.enrich_finding(f)

    result = asyncio.run(orchestrator.trigger_auto_mitigation(f))
    assert result["status"] == "mitigation_initiated"
    assert temporal.anchors[-1].event_type == "auto_mitigation_triggered"
    print(f"   ✅ CVS‑0.4: Mitigação automática acionada para {f.cve}")

def test_cvs_05_sla_tracking():
    """CVS‑0.5: SLA tracking ancorado na TemporalChain."""
    temporal = TemporalChain()
    db = ThreatDatabase()
    guardian = GuardianAttractor(db)
    inventory = Inventory(temporal)
    orchestrator = FleetOrchestrator(temporal)
    engine = MA_S2_Engine(temporal, guardian, inventory, orchestrator)

    findings = asyncio.run(engine.continuous_vulnerability_scan("test-artifact-001"))

    cvs_anchors = [a for a in temporal.anchors if a.event_type == "cvs_scan_complete"]
    assert len(cvs_anchors) >= 1, "Deve haver âncora CVS"
    assert "findings" in cvs_anchors[0].payload
    print(f"   ✅ CVS‑0.5: {len(cvs_anchors)} âncoras de scan, {cvs_anchors[0].payload['findings']} findings")

# ═════════════════════════════════════════════════════════════
# 2. TESTES APM – Attack Path Modeling
# ═════════════════════════════════════════════════════════════

def test_apm_11_path_modeling():
    """APM‑1.1: Modelagem de caminhos de ataque multi‑estágio."""
    db = ThreatDatabase()
    guardian = GuardianAttractor(db)

    service_map = {
        "api-gateway": {"exposure": 1.0, "ports": [443, 80]},
        "auth-service": {"exposure": 0.6, "ports": [8080]},
        "database": {"exposure": 0.2, "ports": [5432]},
        "worker-queue": {"exposure": 0.4, "ports": [6379]},
    }

    paths = guardian.model_attack_paths(service_map)
    assert len(paths) > 0, "Deve modelar pelo menos 1 caminho"
    for p in paths:
        assert len(p.nodes) >= 2, "Caminho deve ter múltiplos nós"
        assert 0.0 <= p.risk_score <= 1.0
    print(f"   ✅ APM‑1.1: {len(paths)} caminhos modelados")

def test_apm_13_contextual_triage():
    """APM‑1.3: Triage contextual com prioridade computada."""
    db = ThreatDatabase()
    guardian = GuardianAttractor(db)

    service_map = {
        "frontend": {"exposure": 0.9},
        "backend": {"exposure": 0.7},
        "db": {"exposure": 0.3},
    }
    paths = guardian.model_attack_paths(service_map)

    for path in paths:
        priority = guardian.compute_contextual_priority(path)
        assert 0.0 <= priority <= 1.0
        assert priority >= path.risk_score * 0.9  # Deve manter base
    print(f"   ✅ APM‑1.3: {len(paths)} prioridades contextuais computadas")

def test_apm_14_mitre_integration():
    """APM‑1.4: Integração MITRE ATT&CK no ThreatDatabase."""
    db = ThreatDatabase()
    intel = db.get_threat_intel("CVE-2026-12345")

    assert "mitre" in intel
    assert len(intel["mitre"]) > 0
    assert "T1190" in intel["mitre"]
    print(f"   ✅ APM‑1.4: MITRE técnicas {intel['mitre']} para CVE-2026-12345")

# ═════════════════════════════════════════════════════════════
# 3. TESTES INV – Inventory & SBOM
# ═════════════════════════════════════════════════════════════

def test_inv_21_sbom_generation():
    """INV‑2.1: SBOM CycloneDX gerada e hash calculada."""
    temporal = TemporalChain()
    inventory = Inventory(temporal)

    release = "arkhe-runtime-v8.0.0-3"
    sbom_str = asyncio.run(inventory.build_sbom(release))
    sbom_hash = hashlib.sha3_256(sbom_str.encode()).hexdigest()

    assert len(sbom_hash) == 64
    assert "CycloneDX" in sbom_str
    assert "components" in sbom_str
    print(f"   ✅ INV‑2.1: SBOM gerada, hash={sbom_hash[:16]}...")

def test_inv_22_runtime_reconciliation():
    """INV‑2.2: Reconciliação contínua detecta drift."""
    temporal = TemporalChain()
    inventory = Inventory(temporal)

    release = "arkhe-runtime-v8.0.0-3"
    asyncio.run(inventory.build_sbom(release))

    # Sem runtime registrado → drift esperado
    result = asyncio.run(inventory.reconcile_runtime(release))
    assert result["drift_detected"] is True
    assert result["missing"]  # Deve listar componentes ausentes
    print(f"   ✅ INV‑2.2: Drift detectado, {len(result['missing'])} componentes ausentes")

def test_inv_25_sbom_anchoring():
    """INV‑2.5: SBOM ancorada na TemporalChain com selo."""
    temporal = TemporalChain()
    db = ThreatDatabase()
    guardian = GuardianAttractor(db)
    inventory = Inventory(temporal)
    orchestrator = FleetOrchestrator(temporal)
    engine = MA_S2_Engine(temporal, guardian, inventory, orchestrator)

    sbom_hash = asyncio.run(engine.generate_sbom("arkhe-v8.0.0"))

    sbom_anchors = [a for a in temporal.anchors if a.event_type == "sbom_anchored"]
    assert len(sbom_anchors) >= 1
    assert sbom_anchors[0].payload["hash"] == sbom_hash
    print(f"   ✅ INV‑2.5: SBOM ancorada com selo {sbom_anchors[0].seal[:16]}...")

# ═════════════════════════════════════════════════════════════
# 4. TESTES ARO – Autonomous Remediation Orchestration
# ═════════════════════════════════════════════════════════════

def test_aro_31_fleet_deploy():
    """ARO‑3.1 / ARO‑3.2: Deploy orquestrado em toda a frota."""
    temporal = TemporalChain()
    orchestrator = FleetOrchestrator(temporal)

    dep_id = asyncio.run(orchestrator.deploy_to_all_environments(
        "arkhe-runtime-v8.0.1",
        change_request_id="fix-CVE-2026-12345",
        respect_change_windows=True
    ))

    assert dep_id.startswith("dep-")
    assert dep_id in orchestrator.deployments
    dep = orchestrator.deployments[dep_id]
    assert dep.status == "completed"
    assert len(dep.environments) >= 4
    print(f"   ✅ ARO‑3.1/3.2: Deploy {dep_id} em {len(dep.environments)} ambientes")

def test_aro_34_suppression_audit():
    """ARO‑3.4: Supressão com trilha de auditoria."""
    temporal = TemporalChain()
    orchestrator = FleetOrchestrator(temporal)

    asyncio.run(orchestrator.suppress_with_audit("CVE-2026-12345", "dep-abc123"))

    assert "CVE-2026-12345" in orchestrator.suppressions
    sup = orchestrator.suppressions["CVE-2026-12345"]
    assert "audit_trail" in sup
    assert sup["audit_trail"]  # Selo temporal não vazio
    print(f"   ✅ ARO‑3.4: Supressão auditada, trail={sup['audit_trail'][:16]}...")

# ═════════════════════════════════════════════════════════════
# 5. TESTE INTEGRADO – Conformidade Completa
# ═════════════════════════════════════════════════════════════

def test_full_ma_s2_compliance():
    """Teste end‑to‑end: todos os 4 domínios em sequência."""
    temporal = TemporalChain()
    db = ThreatDatabase()
    guardian = GuardianAttractor(db)
    inventory = Inventory(temporal)
    orchestrator = FleetOrchestrator(temporal)
    engine = MA_S2_Engine(temporal, guardian, inventory, orchestrator)

    artifact = "arkhe-runtime-v8.0.0-3"

    # CVS
    findings = asyncio.run(engine.continuous_vulnerability_scan(artifact))

    # APM
    service_map = {
        "api-gateway": {"exposure": 1.0},
        "auth-service": {"exposure": 0.6},
        "database": {"exposure": 0.2},
    }
    paths = asyncio.run(engine.attack_path_modeling(service_map))

    # INV
    sbom_hash = asyncio.run(engine.generate_sbom(artifact))

    # ARO
    dep_id = asyncio.run(engine.fleet_wide_patch("CVE-2026-12345", "arkhe-runtime-v8.0.1"))

    # Relatório
    report = engine.generate_compliance_report()

    assert report["overall_status"] == "compliant"
    assert report["chain_integrity"] is True
    assert all(v == "compliant" for v in report["domains"].values())
    assert report["controls_tested"] == 4

    print(f"   ✅ COMPLIANCE FULL: {report['domains']}")
    print(f"   ✅ Temporal seal: {report['temporal_seal'][:24]}...")
    print(f"   ✅ Chain integrity: {report['chain_integrity']}")
    return report

# ═════════════════════════════════════════════════════════════
# EXECUÇÃO
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═"*60)
    print("  ARKHE SUBSTRATO 9008 – MA‑S2 COMPLIANCE ENGINE")
    print("  Test Suite v1.0")
    print("═"*60 + "\n")

    tests = [
        ("CVS‑0.1", test_cvs_01_scan_artifact),
        ("CVS‑0.2", test_cvs_02_epss_kev_enrichment),
        ("CVS‑0.4", test_cvs_04_auto_escalation),
        ("CVS‑0.5", test_cvs_05_sla_tracking),
        ("APM‑1.1", test_apm_11_path_modeling),
        ("APM‑1.3", test_apm_13_contextual_triage),
        ("APM‑1.4", test_apm_14_mitre_integration),
        ("INV‑2.1", test_inv_21_sbom_generation),
        ("INV‑2.2", test_inv_22_runtime_reconciliation),
        ("INV‑2.5", test_inv_25_sbom_anchoring),
        ("ARO‑3.1/3.2", test_aro_31_fleet_deploy),
        ("ARO‑3.4", test_aro_34_suppression_audit),
        ("FULL‑E2E", test_full_ma_s2_compliance),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            print(f"🔷 {name}...", end=" ")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n   ❌ FALHA: {e}")
            failed += 1

    print("\n" + "═"*60)
    print(f"  RESULTADO: {passed} passaram, {failed} falharam")
    print("═"*60)

    if failed == 0:
        # Gera selo canônico
        final_report = test_full_ma_s2_compliance()
        seal_data = json.dumps(final_report, sort_keys=True)
        canonical_seal = hashlib.sha3_256(seal_data.encode()).hexdigest()
        print(f"\n🔒 SELO CANÔNICO 9008: {canonical_seal}")
        sys.exit(0)
    else:
        sys.exit(1)
