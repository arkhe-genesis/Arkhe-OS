import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import os
import logging
from stochastic_resilience import PhaseGradientRedistributor

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def simulate_central_gateways_peak(output_dir: str = "test-results"):
    """
    Simula a observação passiva de 12 gateways principais durante o horário de pico.
    Observa a redistribuição dinâmica de K sob alta carga e entropia urbana.
    """
    logger.info("🏢 Iniciando Observação dos 12 Gateways Principais (Central)")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    n_gateways = 12
    model = PhaseGradientRedistributor(n_gateways, initial_k=1.8)
    optimizer = torch.optim.Adam([model.K], lr=0.02)

    # Fases iniciais (Horário de Pico: Alta Entropia)
    phases = torch.randn(n_gateways)
    alive_mask = torch.ones(n_gateways)

    # Registro de evolução
    history_R = []
    history_K = []

    logger.info("📈 Observando redistribuição passiva...")

    for step in range(100):
        optimizer.zero_grad()
        R, d_theta = model(phases, alive_mask)

        # Perda baseada em coerência urbana
        loss = (1 - R) + 0.005 * torch.norm(model.K)
        loss.backward()
        optimizer.step()

        with torch.no_grad():
            model.K.clamp_(0.5, 4.0)
            phases += d_theta * 0.1
            phases %= 2 * np.pi

        history_R.append(R.item())
        history_K.append(model.K.mean().item())

    # Plot
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history_R, 'cyan')
    plt.title('Coerência Urbana (R)')
    plt.xlabel('Intervalos de Observação')
    plt.ylabel('R')

    plt.subplot(1, 2, 2)
    plt.plot(history_K, 'orange')
    plt.title('Acoplamento Médio (K)')
    plt.xlabel('Intervalos de Observação')
    plt.ylabel('K_mean')

    plot_path = os.path.join(output_dir, "central_peak_observation.png")
    plt.savefig(plot_path)
    plt.close()

    logger.info(f"✅ Observação concluída. R final: {history_R[-1]:.4f}")
    logger.info(f"📊 Gráfico salvo em: {plot_path}")

    return history_R, history_K

if __name__ == "__main__":
    simulate_central_gateways_peak()
