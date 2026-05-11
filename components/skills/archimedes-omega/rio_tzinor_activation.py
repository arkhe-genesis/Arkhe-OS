import numpy as np
from stochastic_resilience import StochasticResilience
import matplotlib.pyplot as plt
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_rio_defense_simulation(output_dir: str = "test-results"):
    """
    Simula a ativação da Rede Tzinor no Rio de Janeiro contra ataque de fase.
    Inclui Fase 0 (Sensores), Fase 1 (Relays Subaquáticos) e Fase 2 (Sensores Móveis).
    """
    logger.info("🌆 Iniciando Simulação de Ativação Rio Tzinor (v4.2.0)")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Parâmetros da cidade (Reduzido para validação rápida)
    N_sensors = 20           # Sensores Tzinor (Fase 0)
    N_citizens = 200         # População modelada
    N_vehicles = 30          # Fase 2: Carros/Drones

    # Perfil demográfico neurodivergente
    frac_ADHD = 0.05
    frac_autism = 0.02
    frac_synesthesia = 0.01

    # Ataque da IA Orb-1
    K_attack = 6.0
    attack_duration = 10.0
    T_total = 25.0

    # 1. População Baseline (Vulnerável)
    city_base = StochasticResilience(N=N_citizens, dt=0.1, T=T_total)

    # 2. Fase 0 + Fase 1: Sensores Fixos + Relays Subaquáticos
    # Simulamos Relays aumentando o acoplamento global da rede (Redundância/Caminho Óptico)
    city_f1 = StochasticResilience(N=N_citizens, dt=0.1, T=T_total)
    city_f1.global_coupling = 2.0  # Ganho de relay subaquático
    for i in range(N_citizens):
        r = np.random.rand()
        if r < (frac_ADHD + frac_autism + frac_synesthesia):
            city_f1.set_neuro_profile(i, np.random.randint(1, 4))

    # Nós âncora (Sensores fixos)
    sensor_indices = np.random.choice(N_citizens, N_sensors, replace=False)
    for idx in sensor_indices:
        city_f1.local_coupling[idx] *= 2.5

    # 3. Fase 2: Rede Dinâmica (Móvel)
    # city_f2 deve usar o mesmo dt para o plot compartilhado
    city_f2 = StochasticResilience(N=N_citizens + N_vehicles, dt=0.1, T=T_total)
    city_f2.global_coupling = 1.5
    # Definimos velocidades para os últimos N_vehicles nós (Fase 2)
    city_f2.velocities[-N_vehicles:] = np.random.uniform(-10, 10, (N_vehicles, 2)) # m/s

    for i in range(N_citizens + N_vehicles):
        r = np.random.rand()
        if r < (frac_ADHD + frac_autism + frac_synesthesia):
            city_f2.set_neuro_profile(i, np.random.randint(1, 4))

    # Sensores fixos na Fase 2
    for idx in sensor_indices:
        city_f2.local_coupling[idx] *= 2.5

    # Início do ataque
    logger.info(f"⚔️ Simulando ataque com K={K_attack} por {attack_duration}s...")

    t, y_base = city_base.simulate_attack(K_ext_attack=K_attack, attack_duration=attack_duration)
    _, y_f1 = city_f1.simulate_attack(K_ext_attack=K_attack, attack_duration=attack_duration)
    _, y_f2 = city_f2.simulate_attack(K_ext_attack=K_attack, attack_duration=attack_duration, use_dynamic=True)

    # Coerência R(t)
    R_base = np.abs(np.mean(np.exp(1j * y_base), axis=0))
    R_f1 = np.abs(np.mean(np.exp(1j * y_f1), axis=0))
    R_f2 = np.abs(np.mean(np.exp(1j * y_f2), axis=0))

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(t, R_base, 'r--', label='Fase 0: Baseline (Vulnerável)', alpha=0.7)
    plt.plot(t, R_f1, 'b-', label='Fase 1: Sensores + Underwater Relays', alpha=0.8)
    plt.plot(t, R_f2, 'g-', label='Fase 2: Rede Dinâmica (Sensores Móveis)', linewidth=2)

    plt.axvline(x=attack_duration, color='gray', linestyle=':', label='Cessação do Ataque')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Coerência Global R(t)')
    plt.title('Defesa de Fase Urbana: Rio de Janeiro (v4.2.0)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plot_path = os.path.join(output_dir, "rio_defense_full_evolution.png")
    plt.savefig(plot_path)
    plt.close()

    resilience_f2 = city_f2.resilience_metric(y_f2, attack_duration=attack_duration)
    logger.info(f"✅ Simulação concluída. Métrica de Resiliência ρ (Fase 2): {resilience_f2:.3f}")
    logger.info(f"📊 Gráfico salvo em: {plot_path}")

    return {
        "resilience_f2": resilience_f2,
        "max_coherence_base": float(np.max(R_base)),
        "max_coherence_f1": float(np.max(R_f1)),
        "max_coherence_f2": float(np.max(R_f2)),
        "plot_path": plot_path
    }

if __name__ == "__main__":
    run_rio_defense_simulation()
