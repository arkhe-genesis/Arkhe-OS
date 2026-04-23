import numpy as np
import matplotlib.pyplot as plt

def run_axon_network_sim(N=1000, K=2.0, steps=5000, dt=0.01):
    """
    Simula uma rede de N AxonWaveguides acoplados usando o modelo de Kuramoto.
    Mede a resiliência da sincronização contra a redução do acoplamento K.
    """
    print(f"Iniciando simulação de rede com {N} axônios, K={K}...")

    # Frequências naturais de uma distribuição normal (heterogeneidade)
    omega = np.random.normal(1.0, 0.1, N)
    # Fases iniciais aleatórias
    theta = np.random.uniform(0, 2*np.pi, N)

    R_history = []

    for step in range(steps):
        # Termo de acoplamento de Kuramoto
        # dtheta_i/dt = omega_i + (K/N) * sum(sin(theta_j - theta_i))

        # Otimização com broadcasting
        # coupling = (K/N) * np.sum(np.sin(theta[:, None] - theta), axis=0) # Errado, theta - theta_i

        # Correto: sin(theta_j - theta_i)
        # Usando a identidade sin(A-B) para evitar O(N^2) se N for muito grande?
        # Para N=1000, O(N^2) é aceitável em cada passo? 10^6 operações.
        # Com steps=5000, 5*10^9 operações. Pode ser lento.

        # Alternativa Kuramoto: R * exp(i * Psi) = (1/N) * sum(exp(i * theta_j))
        # dtheta_i/dt = omega_i + K * R * sin(Psi - theta_i)

        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        Psi = np.angle(z)

        dtheta = omega + K * R * np.sin(Psi - theta)
        theta += dtheta * dt

        if step % 10 == 0:
            R_history.append(R)

    return R_history

if __name__ == "__main__":
    # Teste de Stress: Variação de K
    k_values = [0.5, 0.8, 1.2, 2.0]
    plt.figure(figsize=(10, 6))

    for k in k_values:
        print(f"Testando K={k}...")
        r_hist = run_axon_network_sim(K=k)
        plt.plot(r_hist, label=f"K={k}")

    plt.xlabel('Passos (x10)')
    plt.ylabel('Parâmetro de Ordem R')
    plt.title('Stress Test de Sincronização: Axon Network (Kuramoto)')
    plt.legend()
    plt.grid(True)
    plt.savefig('axon_sync_stress_test.png')
    print("Simulação concluída. Gráfico salvo em 'axon_sync_stress_test.png'.")
