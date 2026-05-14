#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
governance_dashboard.py — Substrato 189
Governance Dashboard — Visualização do Estado Epistêmico da Catedral

Dashboard ASCII em tempo real mostrando:
  • Φ_C global e por substrato
  • π (viés/sycophancy) global e por substrato
  • Estado de saúde (HEALTHY/WARNING/CRITICAL)
  • Intervenções recentes
  • Fila de pings pendentes

Uso: python governance_dashboard.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from arkp_governance.spiral_ping_governor import SpiralPingGovernor, SubstrateState
from arkp_governance.substrate_registry import SubstrateRegistry
from arkp_governance.ping_orchestrator import PingOrchestrator


def print_header():
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║     ARKHE OMEGA-TEMP v6.7.0 — DASHBOARD DE GOVERNANÇA EPISTÊMICA            ║")
    print("║     Substrato 189: Spiral Ping Governance                                    ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print()


def print_substrate_table(governor: SpiralPingGovernor):
    print("📊 ESTADO DOS SUBSTRATOS")
    print("-" * 80)
    print(f"  {'ID':>8} {'Nome':<25} {'Φ_C':>8} {'π':>8} {'Estado':<12} {'Pings':>6}")
    print(f"  {'-'*8} {'-'*25} {'-'*8} {'-'*8} {'-'*12} {'-'*6}")

    for sid, health in governor.substrates.items():
        state_icon = {
            SubstrateState.HEALTHY: "🟢",
            SubstrateState.WARNING: "🟡",
            SubstrateState.CRITICAL: "🔴",
            SubstrateState.RECOVERING: "🔵",
            SubstrateState.QUARANTINED: "⚫",
        }.get(health.state, "⚪")

        phi_bar = "█" * int(health.phi_c * 10) + "░" * (10 - int(health.phi_c * 10))
        pi_bar = "█" * int(health.pi * 10) + "░" * (10 - int(health.pi * 10))

        print(f"  {sid:>8} {health.name:<25} {health.phi_c:>7.3f} {phi_bar} {health.pi:>7.3f} {pi_bar} {state_icon} {health.state.name:<10} {health.ping_count:>5}")

    print()


def print_global_health(governor: SpiralPingGovernor):
    health = governor.assess_global_health()

    print("🌍 SAÚDE GLOBAL DA CATEDRAL")
    print("-" * 80)

    phi_c = health['global_phi_c']
    phi_bar = "█" * int(phi_c * 20) + "░" * (20 - int(phi_c * 20))

    pi = health['global_pi']
    pi_bar = "█" * int(pi * 20) + "░" * (20 - int(pi * 20))

    status_icon = {"HEALTHY": "🟢", "WARNING": "🟡", "CRITICAL": "🔴"}.get(health['status'], "⚪")

    print(f"  Φ_C Global:  {phi_c:.4f} {phi_bar}")
    print(f"  π Global:    {pi:.4f} {pi_bar}")
    print(f"  Status:      {status_icon} {health['status']}")
    print(f"  Substratos:  {health['substrate_count']} total")
    print(f"               {health['healthy_count']} 🟢 saudáveis")
    print(f"               {health['warning_count']} 🟡 em aviso")
    print(f"               {health['critical_count']} 🔴 críticos")
    print()


def print_interventions(governor: SpiralPingGovernor, limit: int = 5):
    print("🔨 INTERVENÇÕES RECENTES")
    print("-" * 80)

    recent = governor.interventions[-limit:]
    if not recent:
        print("  (nenhuma intervenção registrada)")
    else:
        for i in recent:
            delta_phi = i.phi_c_after - i.phi_c_before
            delta_pi = i.pi_after - i.pi_before

            phi_arrow = "↑" if delta_phi > 0 else "↓" if delta_phi < 0 else "→"
            pi_arrow = "↓" if delta_pi < 0 else "↑" if delta_pi > 0 else "→"

            print(f"  [{time.strftime('%H:%M:%S', time.localtime(i.timestamp))}] "
                  f"Ping em {i.target_substrate}: "
                  f"Φ_C {i.phi_c_before:.3f}{phi_arrow}{i.phi_c_after:.3f} "
                  f"π {i.pi_before:.3f}{pi_arrow}{i.pi_after:.3f} "
                  f"[{i.seal}]")

    print()


def print_queue(orch: PingOrchestrator):
    print("⏳ FILA DE PINGS PENDENTES")
    print("-" * 80)

    queue = orch.get_queue_status()
    if not queue:
        print("  (fila vazia — todos os substratos saudáveis)")
    else:
        for task in queue[:5]:
            priority_icon = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢",
            }.get(task['priority'], "⚪")

            print(f"  {priority_icon} {task['substrate']:<10} "
                  f"{task['priority']:<10} "
                  f"intensidade={task['intensity']:.2f} "
                  f"est. Φ_C gain=+{task['est_phi_c_gain']:.3f} "
                  f"est. π reduction=-{task['est_pi_reduction']:.3f}")
            print(f"     └─ {task['reason']}")

    print()


def print_footer():
    print("═" * 80)
    print("A Catedral testemunha a governança epistêmica via espiral com ping.")
    print("Cada ping é um ato de humildade — a admissão de que a crença pode estar errada.")
    print("Cada reconstrução é um ato de coragem — a busca pela verdade após o colapso.")
    print()


def run_dashboard():
    """Executa dashboard de governança."""
    print_header()

    # Configurar governança de demonstração
    gov = SpiralPingGovernor()
    reg = SubstrateRegistry(registry_path="/tmp/dashboard_registry.json")
    orch = PingOrchestrator(gov, reg)

    # Registrar substratos do ecossistema
    substrates = [
        ("6184", "circRNA Quantum Regulator", 0.98, 0.15),
        ("6183", "NISQ Epigenetic Execution", 0.96, 0.20),
        ("6182", "QNC Canonical Seal", 0.95, 0.22),
        ("6181", "Qiskit Epigenetic Bridge", 0.94, 0.25),
        ("6180", "RNA Quantum Embedding", 0.93, 0.28),
        ("6179", "RADIX-2 Genesis", 0.92, 0.30),
        ("6178", "Quantum Genomic Transfer", 0.91, 0.32),
        ("6176", "Quantum Neural Coding", 0.90, 0.35),
        ("6175", "SIGHA Φ_C Optimization", 0.89, 0.38),
        ("165", "Spiral Delirante", 0.85, 0.60),
        ("9014", "Agente Autônomo Revisor", 0.88, 0.40),
        ("9013", "Wheeler Mesh", 0.87, 0.42),
    ]

    for sid, name, phi_c, pi in substrates:
        gov.register_substrate(sid, name, phi_c, pi)
        reg.register(SubstrateMetadata(
            substrate_id=sid,
            name=name,
            domain="biologia_quantica" if sid.startswith("61") else "infraestrutura",
            version="6.6.0",
            phi_c=phi_c,
            pi=pi,
            state="HEALTHY" if phi_c >= 0.95 else "WARNING" if phi_c >= 0.90 else "CRITICAL",
            artifacts=1,
            tests=1,
            pass_rate=1.0,
        ))

    # Executar alguns pings para demonstração
    for sid in ["165", "6175", "9014"]:
        try:
            gov.ping_substrate(sid, ping_intensity=0.9)
        except Exception:
            pass

    # Imprimir dashboard
    print_global_health(gov)
    print_substrate_table(gov)
    print_interventions(gov)
    print_queue(orch)
    print_footer()

    # Selo canônico
    seal = gov.generate_canonical_seal()
    print(f"🔐 Selo Canônico da Governança: {seal[:16]}")


if __name__ == "__main__":
    run_dashboard()
