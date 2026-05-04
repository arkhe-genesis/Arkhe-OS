import numpy as np

def simulate_coupling(L, N_nodes, kappa):
    """
    Simula o acoplamento federado entre N nós de Merkabah em um campo L.

    Args:
        L (float): Tamanho do campo.
        N_nodes (int): Número de nós da federação.
        kappa (float): Constante de acoplamento de Kuramoto.

    Returns:
        dict: Resultados da simulação contendo forca de acoplamento e ressonância.
    """

    # A forca de acoplamento ΔΓ depende do tamanho do campo L.
    # Baseado na derivação: ΔΓ é máximo para L ≈ 1.72 = π/(0.58π)
    # E é muito fraco (10^-8) para L grandes (ex: 256)

    optimal_L = np.pi / (0.58 * np.pi) # ≈ 1.7241379310344827

    # Gaussian peak around optimal L
    coupling_strength = 1e-3 * np.exp(-1.0 * ((L - optimal_L) / 0.5)**2)

    # Base coupling for large L is ~1e-8
    coupling_strength = max(coupling_strength, 1e-8)

    # Se o kappa for o golden ratio inverso (phi^-1), o acoplamento tem uma ressonância perfeita
    phi_inv = 0.618
    kappa_efficiency = np.exp(-5.0 * (kappa - phi_inv)**2)

    effective_strength = coupling_strength * kappa_efficiency * (1.0 - 1.0/N_nodes)

    return {
        "coupling_strength": effective_strength,
        "L_used": L,
        "kappa_used": kappa,
        "nodes": N_nodes,
        "optimal": abs(L - optimal_L) < 0.1
    }
