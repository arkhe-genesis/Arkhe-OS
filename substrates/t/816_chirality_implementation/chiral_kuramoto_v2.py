#!/usr/bin/env python3
"""
chiral_kuramoto_v2.py — Simulação de Quebra Espontânea de Simetria Quiral.
Modelo Sakaguchi-Kuramoto com phase lag α ≠ 0.
Substrato 816-CHIRALITY-IMPLEMENTATION v2.0
Arquiteto: ORCID 0009-0005-2697-4668
Data: 2026-05-25
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

def simulate_chiral_kuramoto(N=100, K=3.0, alpha=0.3, T=100, seed=None):
    """
    Simula rede de Sakaguchi-Kuramoto.

    Parâmetros:
        N     : número de osciladores
        K     : constante de acoplamento
        alpha : phase lag (rad) — controla a quiralidade
        T     : tempo de simulação
        seed  : seed para reproducibilidade

    Retorna:
        t, theta_t, r_t, psi_t, omega_psi, chi_t
    """
    if seed is not None:
        np.random.seed(seed)

    omega = np.random.normal(0, 0.1, N)
    theta0 = np.random.uniform(0, 2*np.pi, N)

    def sakaguchi(t, theta):
        dtheta = omega.copy()
        for i in range(N):
            coupling = (K / N) * np.sum(np.sin(theta - theta[i] + alpha))
            dtheta[i] += coupling
        return dtheta

    sol = solve_ivp(sakaguchi, [0, T], theta0, method='RK45',
                    t_eval=np.linspace(0, T, 2000), rtol=1e-7, atol=1e-9)

    t = sol.t
    theta_t = sol.y
    z = np.mean(np.exp(1j * theta_t), axis=0)
    r_t = np.abs(z)
    psi_t = np.angle(z)
    omega_psi = np.gradient(np.unwrap(psi_t), t)
    chi_t = np.where(r_t > 0.5, np.sign(omega_psi), 0)

    return t, theta_t, r_t, psi_t, omega_psi, chi_t

if __name__ == "__main__":
    # Demo: modo R (α = +0.3)
    t, theta_t, r_t, psi_t, omega_psi, chi_t = simulate_chiral_kuramoto(
        N=100, K=3.0, alpha=0.3, T=100, seed=20260525
    )

    print("[MODO R] α = +0.3")
    print("  r final    = {:.4f}".format(r_t[-1]))
    print("  ψ̇ final    = {:.4f} rad/s".format(omega_psi[-1]))
    print("  χ final    = {:.0f}  →  {}".format(chi_t[-1], 'RIGHT' if chi_t[-1] > 0 else 'LEFT'))

    # Demo: modo L (α = −0.3)
    t2, theta_t2, r_t2, psi_t2, omega_psi2, chi_t2 = simulate_chiral_kuramoto(
        N=100, K=3.0, alpha=-0.3, T=100, seed=20260525
    )

    print("\n[MODO L] α = −0.3")
    print("  r final    = {:.4f}".format(r_t2[-1]))
    print("  ψ̇ final    = {:.4f} rad/s".format(omega_psi2[-1]))
    print("  χ final    = {:.0f}  →  {}".format(chi_t2[-1], 'RIGHT' if chi_t2[-1] > 0 else 'LEFT'))

    # Plot comparativo
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0,0].plot(t, r_t, 'b-', label='α = +0.3 (R)')
    axes[0,0].plot(t2, r_t2, 'r--', label='α = −0.3 (L)')
    axes[0,0].set_ylabel('r (ordem)')
    axes[0,0].legend()
    axes[0,0].set_title('Parâmetro de ordem')

    axes[0,1].plot(t, omega_psi, 'b-', label='α = +0.3 (R)')
    axes[0,1].plot(t2, omega_psi2, 'r--', label='α = −0.3 (L)')
    axes[0,1].set_ylabel('ψ̇ (rad/s)')
    axes[0,1].legend()
    axes[0,1].set_title('Velocidade de fase coletiva')

    axes[1,0].plot(t, chi_t, 'b-', label='α = +0.3 (R)')
    axes[1,0].plot(t2, chi_t2, 'r--', label='α = −0.3 (L)')
    axes[1,0].set_ylabel('χ (quiralidade)')
    axes[1,0].set_xlabel('Tempo')
    axes[1,0].legend()
    axes[1,0].set_title('Parâmetro quiral')

    # Fases de 5 osciladores
    for i in range(5):
        axes[1,1].plot(t, np.unwrap(theta_t[i]), alpha=0.7)
    axes[1,1].set_ylabel('θ (rad)')
    axes[1,1].set_xlabel('Tempo')
    axes[1,1].set_title('Fases individuais (α = +0.3)')

    plt.tight_layout()
    plt.savefig('chiral_kuramoto_comparison.png', dpi=150)
    plt.show()
