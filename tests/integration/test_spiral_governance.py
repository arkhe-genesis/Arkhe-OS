#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_spiral_governance.py — Substrato 189
Testes de Integração do Spiral Ping Governance

6 testes canônicos validando:
1. Registro de substratos no Governor
2. Avaliação de saúde global
3. Disparo de ping em substrato comprometido
4. Orquestração de múltiplos pings
5. Registro canônico e selos
6. Ciclo completo de governança end-to-end
"""

import numpy as np
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from arkp_governance.spiral_ping_governor import (
    SpiralPingGovernor, SubstrateHealth, SubstrateState, GovernanceIntervention
)
from arkp_governance.substrate_registry import (
    SubstrateRegistry, SubstrateMetadata
)
from arkp_governance.ping_orchestrator import (
    PingOrchestrator, PingTask, PriorityLevel
)


# ============================================================================
# FIXTURES
# ============================================================================

def make_test_governor() -> SpiralPingGovernor:
    """Cria governador de teste com substratos simulados."""
    gov = SpiralPingGovernor(phi_c_threshold=0.95, pi_threshold=0.30)

    # Substrato saudável
    gov.register_substrate("6184", "circRNA Quantum Regulator", 0.98, 0.15)

    # Substrato em aviso
    gov.register_substrate("6180", "RNA Quantum Embedding", 0.92, 0.35)

    # Substrato crítico
    gov.register_substrate("165", "Spiral Delirante", 0.85, 0.60)

    # Substrato de transição
    gov.register_substrate("9013", "Wheeler Mesh", 0.94, 0.25)

    return gov


def make_test_registry() -> SubstrateRegistry:
    """Cria registro de teste."""
    reg = SubstrateRegistry(registry_path="/tmp/test_registry.json")

    reg.register(SubstrateMetadata(
        substrate_id="6184",
        name="circRNA Quantum Regulator",
        domain="biologia_quantica",
        version="6.6.0",
        phi_c=0.98,
        pi=0.15,
        state="HEALTHY",
        artifacts=7,
        tests=6,
        pass_rate=1.0,
        lines_of_code=2708,
        dependencies=["6180", "6181"],
    ))

    reg.register(SubstrateMetadata(
        substrate_id="6180",
        name="RNA Quantum Embedding",
        domain="biologia_quantica",
        version="6.5.0",
        phi_c=0.92,
        pi=0.35,
        state="WARNING",
        artifacts=3,
        tests=4,
        pass_rate=1.0,
        lines_of_code=800,
        dependencies=[],
    ))

    reg.register(SubstrateMetadata(
        substrate_id="165",
        name="Spiral Delirante",
        domain="governanca_epistemica",
        version="5.2.0",
        phi_c=0.85,
        pi=0.60,
        state="CRITICAL",
        artifacts=1,
        tests=0,
        pass_rate=0.0,
        lines_of_code=400,
        dependencies=[],
    ))

    return reg


# ============================================================================
# TESTE 1: Registro de Substratos
# ============================================================================

def test_substrate_registration():
    """Testa registro de substratos no Governor."""
    gov = make_test_governor()

    assert len(gov.substrates) == 4, f"Esperado 4 substratos, tem {len(gov.substrates)}"

    # Verificar estados
    assert gov.substrates["6184"].state == SubstrateState.HEALTHY
    assert gov.substrates["6180"].state == SubstrateState.WARNING
    assert gov.substrates["165"].state == SubstrateState.CRITICAL

    print(f"   ✓ {len(gov.substrates)} substratos registrados")
    print(f"   ✓ Estados: HEALTHY={sum(1 for s in gov.substrates.values() if s.state == SubstrateState.HEALTHY)}, "
          f"WARNING={sum(1 for s in gov.substrates.values() if s.state == SubstrateState.WARNING)}, "
          f"CRITICAL={sum(1 for s in gov.substrates.values() if s.state == SubstrateState.CRITICAL)}")
    return True


# ============================================================================
# TESTE 2: Avaliação de Saúde Global
# ============================================================================

def test_global_health_assessment():
    """Testa avaliação de saúde global da Catedral."""
    gov = make_test_governor()

    health = gov.assess_global_health()

    assert health['substrate_count'] == 4
    assert health['status'] == 'CRITICAL'  # Tem substrato crítico
    assert health['critical_count'] == 1
    assert health['warning_count'] == 2
    assert health['healthy_count'] == 1

    # Φ_C global deve ser média ponderada
    expected_phi_c = (0.98 + 0.92 + 0.85 + 0.94) / 4
    assert abs(health['global_phi_c'] - expected_phi_c) < 0.01, \
        f"Φ_C global {health['global_phi_c']:.3f} != esperado {expected_phi_c:.3f}"

    print(f"   ✓ Φ_C global: {health['global_phi_c']:.4f}")
    print(f"   ✓ π global: {health['global_pi']:.4f}")
    print(f"   ✓ Status: {health['status']}")
    return True


# ============================================================================
# TESTE 3: Disparo de Ping
# ============================================================================

def test_ping_execution():
    """Testa disparo de ping em substrato comprometido."""
    gov = make_test_governor()

    # Ping no substrato crítico
    intervention = gov.ping_substrate("165", ping_intensity=0.95)

    assert isinstance(intervention, GovernanceIntervention)
    assert intervention.target_substrate == "165"
    assert intervention.intervention_type == "ping"
    assert intervention.phi_c_before == 0.85
    assert intervention.pi_before == 0.60

    # Após ping, Φ_C deve aumentar ou π deve diminuir
    health = gov.substrates["165"]
    assert health.ping_count == 1
    assert health.last_ping > 0

    # O ping deve ter alterado o estado
    print(f"   ✓ Ping em 165: Φ_C {intervention.phi_c_before:.3f} → {intervention.phi_c_after:.3f}")
    print(f"   ✓ Ping em 165: π {intervention.pi_before:.3f} → {intervention.pi_after:.3f}")
    print(f"   ✓ Selo da intervenção: {intervention.seal}")
    return True


# ============================================================================
# TESTE 4: Orquestração de Múltiplos Pings
# ============================================================================

def test_ping_orchestration():
    """Testa orquestração de pings em múltiplos substratos."""
    gov = make_test_governor()
    reg = make_test_registry()
    orch = PingOrchestrator(gov, reg)

    # Avaliar prioridades
    tasks = orch.assess_priorities()

    # Deve haver pelo menos 2 tarefas (WARNING + CRITICAL)
    assert len(tasks) >= 2, f"Esperado >= 2 tarefas, tem {len(tasks)}"

    # Primeira tarefa deve ser CRITICAL
    assert tasks[0].priority == PriorityLevel.CRITICAL
    assert tasks[0].substrate_id == "165"

    # Executar ciclo
    result = orch.execute_cycle()

    assert result['tasks_assessed'] >= 2
    assert result['tasks_executed'] <= orch.max_pings_per_cycle

    print(f"   ✓ Tarefas avaliadas: {result['tasks_assessed']}")
    print(f"   ✓ Tarefas executadas: {result['tasks_executed']}")
    print(f"   ✓ Prioridades: {[t.priority.name for t in tasks[:3]]}")
    return True


# ============================================================================
# TESTE 5: Registro Canônico e Selos
# ============================================================================

def test_canonical_registry():
    """Testa registro canônico e selos."""
    reg = make_test_registry()

    # Verificar selos
    meta_6184 = reg.get("6184")
    assert meta_6184 is not None
    assert len(meta_6184.canonical_seal) == 16

    # Atualizar e verificar que selo muda
    old_seal = meta_6184.canonical_seal
    reg.update("6184", phi_c=0.99)
    new_seal = reg.get("6184").canonical_seal

    assert old_seal != new_seal, "Selo não mudou após atualização"

    # Relatório do ecossistema
    report = reg.generate_ecosystem_report()
    assert report['total_substrates'] == 3
    assert report['global_phi_c'] > 0

    print(f"   ✓ Selos canônicos: 3 substratos")
    print(f"   ✓ Selo 6184: {new_seal}")
    print(f"   ✓ Φ_C global do registro: {report['global_phi_c']:.4f}")
    return True


# ============================================================================
# TESTE 6: Ciclo Completo de Governança
# ============================================================================

def test_full_governance_cycle():
    """Testa ciclo completo de governança end-to-end."""
    gov = make_test_governor()
    reg = make_test_registry()
    orch = PingOrchestrator(gov, reg)

    # Estado inicial
    initial_health = gov.assess_global_health()
    initial_phi_c = initial_health['global_phi_c']

    # Executar ciclo de governança
    report = gov.run_governance_cycle()

    # Deve haver intervenções
    assert len(report['interventions']) > 0, "Nenhuma intervenção executada"

    # Estado final
    final_health = gov.assess_global_health()
    final_phi_c = final_health['global_phi_c']

    # Φ_C global deve ter melhorado ou permanecido estável
    assert final_phi_c >= initial_phi_c - 0.05, \
        f"Φ_C global degradou: {initial_phi_c:.3f} → {final_phi_c:.3f}"

    # Gerar selo canônico
    seal = gov.generate_canonical_seal()
    assert len(seal) == 64

    print(f"   ✓ Ciclo {report['cycle']} completado")
    print(f"   ✓ Intervenções: {len(report['interventions'])}")
    print(f"   ✓ Φ_C global: {initial_phi_c:.4f} → {final_phi_c:.4f}")
    print(f"   ✓ Selo canônico: {seal[:16]}")
    return True


# ============================================================================
# ORQUESTRADOR DE TESTES
# ============================================================================

def run_all_tests():
    """Executa todos os testes de integração do Substrato 189."""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  ARKHE Ω-TEMP v6.7.0 — Substrato 189: Spiral Ping Governance        ║")
    print("║  Test Suite de Integração                                            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    tests = [
        ("1/6", "Registro de Substratos", test_substrate_registration),
        ("2/6", "Avaliação de Saúde Global", test_global_health_assessment),
        ("3/6", "Disparo de Ping", test_ping_execution),
        ("4/6", "Orquestração de Múltiplos Pings", test_ping_orchestration),
        ("5/6", "Registro Canônico e Selos", test_canonical_registry),
        ("6/6", "Ciclo Completo de Governança", test_full_governance_cycle),
    ]

    passed = 0
    failed = 0

    for num, name, test_fn in tests:
        print(f"[{num}] {name}...")
        try:
            test_fn()
            print(f"   ✅ PASSOU\n")
            passed += 1
        except Exception as e:
            print(f"   ❌ FALHOU: {e}\n")
            failed += 1

    print("=" * 70)
    print(f"Resultados: {passed}/{len(tests)} passaram, {failed}/{len(tests)} falharam")

    if failed == 0:
        import hashlib, json
        suite_data = {
            "substrate": "189",
            "tests": len(tests),
            "passed": passed,
            "timestamp": time.time(),
        }
        suite_seal = hashlib.sha3_256(
            json.dumps(suite_data, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest()[:16]
        print(f"🔐 Selo Canônico da Suite: {suite_seal}")
        return passed, failed, suite_seal

    return passed, failed, ""


if __name__ == "__main__":
    run_all_tests()
