#!/usr/bin/env python3
"""
vortex_federation_demo.py — Demonstração de federação quântica sem comunicação clássica.
Mostra N partículas emaranhadas via vórtice agregando gradientes sem trocar bits.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
from vortex_entanglement.multi_particle_vortex import MultiParticleVortex, VortexFiberConfig
from federated_vortex.federated_vortex_aggregator import VortexFederatedAggregator, VortexFederatedConfig

def demo_vortex_federation(num_particles: int = 4, steps: int = 200):
    """Demonstra agregação federada via vórtice com verificação de Bell."""

    print("🌀 ARKHE OS v164 — Demonstração: Federação por Vórtice Emaranhado")
    print("=" * 80)

    # Configurar fibras com torção áurea
    fiber_configs = []
    for i in range(num_particles):
        fiber_configs.append(VortexFiberConfig(
            particle_id=f"particle_{i}",
            initial_position=i * 2.0,  # posições equidistantes
            phase_offset=i * np.pi / num_particles,  # fases equidistantes
            golden_twist=17.03  # torção áurea
        ))

    # Configurar agregador federado
    vortex_config = VortexFederatedConfig(
        num_particles=num_particles,
        fiber_configs=fiber_configs,
        learning_rate=0.01,
        aggregation_window=20,
        add_dp_noise=False  # desativar DP para demonstração clara
    )

    aggregator = VortexFederatedAggregator(vortex_config)

    # Histórico para plot
    history = {
        'rounds': [],
        'avg_loss': [],
        'bell_S_values': [],
        'fidelities': [],
        'phase_updates': []
    }

    print(f"\n📊 Executando {steps} passos de aprendizado federado por vórtice...")

    for step in range(steps):
        # 1. Simular computação local em cada partícula
        for i, cfg in enumerate(fiber_configs):
            # Gradiente simulado: direção aleatória com viés para mínimo
            true_minimum = np.random.randn(50) * 0.1
            gradient = true_minimum + np.random.randn(50) * 0.05 * (1 - step/steps)
            loss = 0.5 * np.linalg.norm(gradient)**2 + np.random.randn() * 0.01

            aggregator.submit_local_gradient(
                participant_id=cfg.particle_id,
                gradient=gradient,
                loss_value=loss,
                metadata={'step': step}
            )

        # 2. Agregação periódica via vórtice
        if step % vortex_config.aggregation_window == 0 and step > 0:
            agg_result = aggregator.perform_vortex_aggregation()

            if agg_result['status'] == 'success':
                history['rounds'].append(agg_result['round'])
                history['avg_loss'].append(agg_result.get('avg_loss', 0))
                history['phase_updates'].append(agg_result['phase_update'])

                # Métricas de emaranhamento
                ent_metrics = aggregator.vortex.get_entanglement_metrics()
                avg_fidelity = np.mean([v for k, v in ent_metrics.items() if 'fidelity' in k])
                history['fidelities'].append(avg_fidelity)

                # Verificação de Bell
                if num_particles >= 2:
                    bell = aggregator.vortex.compute_bell_correlation(
                        fiber_configs[0].particle_id,
                        fiber_configs[1].particle_id
                    )
                    history['bell_S_values'].append(bell['bell_S'])

                    if step % 50 == 0:
                        status = "✓ VIOLAÇÃO" if bell['bell_S'] > 2.0 else "✗ Clássico"
                        print(f"  Round {agg_result['round']}: Loss={agg_result.get('avg_loss', 0):.3f}, "
                              f"Fidelity={avg_fidelity:.3f}, Bell-S={bell['bell_S']:.3f} {status}")

        # 3. Evolução contínua do vórtice
        for cfg in fiber_configs:
            aggregator.vortex.evolve_particle(cfg.particle_id, t_final=0.1)

    # Plot resultados
    plot_federation_results(history, num_particles)

    # Relatório final
    print(f"\n✅ Demonstração concluída")
    print(f"   • Rounds de federação: {len(history['rounds'])}")
    if history['bell_S_values']:
        final_bell = history['bell_S_values'][-1]
        print(f"   • Bell-S final: {final_bell:.3f} {'(emaranhado ✓)' if final_bell > 2.0 else '(clássico ✗)'}")
    if history['fidelities']:
        print(f"   • Fidelidade média final: {history['fidelities'][-1]:.3f}")

    return aggregator, history

def plot_federation_results(history: Dict, num_particles: int):
    """Plota resultados da demonstração de federação."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Perda média vs rounds
    if history['rounds'] and history['avg_loss']:
        ax = axes[0, 0]
        ax.plot(history['rounds'], history['avg_loss'], 'b-o', markersize=4)
        ax.set_xlabel('Round de Federação')
        ax.set_ylabel('Perda Média')
        ax.set_title('Convergência do Aprendizado Federado')
        ax.grid(True, alpha=0.3)

    # 2. Parâmetro S de Bell vs rounds
    if history['rounds'] and history['bell_S_values']:
        ax = axes[0, 1]
        ax.plot(history['rounds'], history['bell_S_values'], 'r-o', markersize=4, label='Bell-S')
        ax.axhline(2.0, color='gray', linestyle='--', label='Limite Clássico')
        ax.axhline(2*np.sqrt(2), color='green', linestyle=':', label='Máximo Quântico')
        ax.set_xlabel('Round de Federação')
        ax.set_ylabel('Parâmetro S de Bell')
        ax.set_title('Verificação de Emaranhamento')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # 3. Fidelidade ao estado agregado
    if history['rounds'] and history['fidelities']:
        ax = axes[1, 0]
        ax.plot(history['rounds'], history['fidelities'], 'g-o', markersize=4)
        ax.set_xlabel('Round de Federação')
        ax.set_ylabel('Fidelidade Média')
        ax.set_title('Coerência com Estado Agregado')
        ax.grid(True, alpha=0.3)

    # 4. Atualizações de fase (conexão de Berry)
    if history['rounds'] and history['phase_updates']:
        ax = axes[1, 1]
        ax.plot(history['rounds'], np.abs(history['phase_updates']), 'm-o', markersize=4)
        ax.set_xlabel('Round de Federação')
        ax.set_ylabel('Magnitude da Atualização de Fase')
        ax.set_title('Evolução da Conexão de Berry')
        ax.grid(True, alpha=0.3)

    plt.suptitle(f'Federação por Vórtice Emaranhado ({num_particles} partículas)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('vortex_federation_demo.png', dpi=150, bbox_inches='tight')
    print(f"📈 Gráficos salvos em vortex_federation_demo.png")
    # plt.show() # Disabled to prevent blocking

if __name__ == "__main__":
    # Executar demonstração
    aggregator, history = demo_vortex_federation(num_particles=4, steps=5)

    # Exportar log de auditoria
    aggregator.export_audit_log('vortex_federation_audit.json')
    print("📋 Log de auditoria exportado para vortex_federation_audit.json")