import numpy as np

def allan_deviation(y, tau0):
    """
    Calcula a variância de Allan (σ_y) para uma série temporal de desvios de frequência y.
    y: fractional frequency deviations
    tau0: sampling interval
    """
    N = len(y)
    max_m = N // 2
    taus = []
    ades = []

    # Seleciona m em escala logarítmica para taus
    m_values = np.unique(np.geomspace(1, max_m, 20, dtype=int))

    for m in m_values:
        tau = m * tau0
        # Variância de Allan (overlapping)
        # σ²_y(τ) = 1 / (2 * (N - 2m)) * sum_{i=1}^{N-2m} (y'_{i+m} - y'_i)²
        # onde y' é a média de y no intervalo m

        # Médias em janelas de m
        y_bar = np.convolve(y, np.ones(m)/m, mode='valid')

        # Diferenças entre janelas adjacentes
        diff = y_bar[m:] - y_bar[:-m]
        sigma_sq = np.mean(diff**2) / 2

        taus.append(tau)
        ades.append(np.sqrt(sigma_sq))

    return np.array(taus), np.array(ades)

def simulate_clocks(duration_s=10000, dt=1.0):
    """
    Simula desvios de frequência fracionária para diferentes relógios.
    """
    N = int(duration_s / dt)

    # 1. Axon Clock (Kuramoto Global)
    # Ruído browniano de fase (White Frequency Noise)
    # Estabilidade em torno de 10^-3 at 1s
    axon_noise = np.random.normal(0, 1e-3, N)

    # 2. Sapphire Clock (Substrato 25)
    # Ultra-estável, noise floor muito baixo (10^-15 at 1s)
    sapphire_noise = np.random.normal(0, 1e-15, N)

    # 3. NV Center Clock (Substrato 27)
    # Estabilidade limitada por decoerência (10^-4 at 1s)
    # Com algum drift (Random Walk Frequency Noise)
    nv_white = np.random.normal(0, 1e-4, N)
    nv_drift = np.cumsum(np.random.normal(0, 1e-6, N))
    nv_noise = nv_white + nv_drift

    return axon_noise, sapphire_noise, nv_noise

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    dt = 1.0
    axon, sapphire, nv = simulate_clocks(duration_s=100000, dt=dt)

    print("Calculando Desvio de Allan...")
    t_axon, a_axon = allan_deviation(axon, dt)
    t_sapph, a_sapph = allan_deviation(sapphire, dt)
    t_nv, a_nv = allan_deviation(nv, dt)

    plt.figure(figsize=(10, 7))
    plt.loglog(t_axon, a_axon, 'r-o', label='AxonClock (Bio-Rhythm)')
    plt.loglog(t_sapph, a_sapph, 'b-s', label='Sapphire Clock (Substrate 25)')
    plt.loglog(t_nv, a_nv, 'g-^', label='NV Center Clock (Substrate 27)')

    plt.xlabel('Intervalo τ (s)')
    plt.ylabel('Desvio de Allan σ_y(τ)')
    plt.title('Comparação de Estabilidade de Relógios da Catedral')
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.savefig('clock_stability_comparison.png')
    print("Concluído. Gráfico salvo em 'clock_stability_comparison.png'.")
