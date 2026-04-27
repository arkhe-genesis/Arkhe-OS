"""
ARKHE OS v64 — SÓLITON PRIMORDIAL v2.0
=======================================
Método: Split-Step Fourier com Strang Splitting
Equação Mestra: ∂Ψ/∂t = (λ - β|Ψ|²)Ψ + D∇²Ψ + κΔ_kΨ - iω_φ Ψ + χΦ_Δ(t)W(t)Ψ + ξ
"""

import numpy as np
from numpy.fft import fft, ifft, fftfreq, fftshift

class PrimordialSolitonSimulation:
    def __init__(self, N=512, L=100.0, dt=0.004):
        # Razão áurea φ ≈ 1.618034
        self.PHI = (1 + np.sqrt(5)) / 2
        self.INV_PHI = 1.0 / self.PHI

        self.N = N
        self.L = L
        self.dt = dt
        self.dx = L / N
        self.x = np.linspace(-L/2, L/2, N, endpoint=False)
        self.k_freq = fftfreq(N, self.dx) * 2 * np.pi

        # Parâmetros da Equação Mestra
        self.LAMBDA_D = 1.0
        self.BETA_D = 1.0
        self.D_COEFF = 0.06
        self.KAPPA = 0.35
        self.THRESHOLD_DK = 0.65
        self.OMEGA_GAUGE = 2 * np.pi * self.INV_PHI
        self.CHI_DELTA = 0.25
        self.W_SIGMA = 0.8
        self.XI_AMP = 0.015

        # Modos de Fibonacci
        self.N_FIB = 14
        self.fib_ns = np.arange(-self.N_FIB // 2, self.N_FIB // 2 + 1).astype(float)
        # Fix: Ensure PHI is used correctly
        self.k_fibonacci = (2 * np.pi / L) * (self.PHI ** self.fib_ns)
        # Ensure k_fibonacci doesn't have zeros that could cause division by zero in validator
        self.k_fibonacci = self.k_fibonacci[self.k_fibonacci != 0]

        # Máscaras de ressonância
        self.RESONANCE_WIDTH = 0.12 # Original narrow
        self.fib_masks = []
        for kf in self.k_fibonacci:
            mask = (np.exp(-(self.k_freq - kf)**2 / (2 * self.RESONANCE_WIDTH**2)) +
                    np.exp(-(self.k_freq + kf)**2 / (2 * self.RESONANCE_WIDTH**2)))
            self.fib_masks.append(mask)

        # Propagadores Lineares
        self.linear_half = np.exp((-self.D_COEFF * self.k_freq**2 - 1j * self.OMEGA_GAUGE) * dt / 2)
        dealias = np.abs(self.k_freq) < (2 * np.pi / (3 * self.dx))
        self.linear_half *= dealias

        # Estado inicial
        self.Psi = self._initialize_field()

    def _initialize_field(self):
        np.random.seed(137)
        Psi = 0.04 * (np.random.randn(self.N) + 1j * np.random.randn(self.N))
        seeds = [
            {'x0': 0.0,  'A': 0.7, 'w': 3.0, 'kp': self.PHI**0},
            {'x0': 18.0, 'A': 0.5, 'w': 2.5, 'kp': self.PHI**1},
            {'x0': -20.0,'A': 0.45,'w': 2.8, 'kp': -self.PHI**2},
        ]
        for s in seeds:
            Psi += s['A'] * np.exp(-(self.x - s['x0'])**2 / (2 * s['w']**2)) * \
                   np.exp(1j * s['kp'] * self.x * 0.1)
        return Psi

    def compute_delta_k(self, Psi_real, Psi_hat):
        rho = np.abs(Psi_real) ** 2
        rho = np.clip(rho, 0, 10.0)
        rho_max = np.max(rho)
        if rho_max < self.THRESHOLD_DK:
            return np.zeros(self.N, dtype=complex)

        activation = np.tanh(3.0 * (rho_max - self.THRESHOLD_DK) / self.THRESHOLD_DK)
        rho_weighted = np.mean(rho[rho > self.THRESHOLD_DK * 0.5])

        delta = np.zeros(self.N, dtype=complex)
        for mask in self.fib_masks:
            delta += ifft(mask * Psi_hat)

        # Add safety factor to prevent runaway feedback
        delta = np.clip(delta, -5.0, 5.0)
        return delta * self.KAPPA * activation * rho_weighted

    def observer_intention(self, t):
        t0 = 8.0
        t_pulses = t0 * self.PHI ** np.array([0, 1, 2, 3])
        sigma_pulse = 0.6
        intention = 0.0
        for tp in t_pulses:
            intention += np.exp(-(t - tp) ** 2 / (2 * sigma_pulse ** 2))
        return np.clip(intention, 0, 1.0)

    def recognition_filter(self, t):
        return np.exp(-(t % self.PHI) ** 2 / (2 * self.W_SIGMA ** 2))

    def nonlinear_step(self, Psi_real, Psi_hat, t):
        rho = np.abs(Psi_real) ** 2
        # Add safety to prevent overflow
        rho = np.clip(rho, 0, 10.0)
        f = self.LAMBDA_D * Psi_real - self.BETA_D * rho * Psi_real
        f += self.compute_delta_k(Psi_real, Psi_hat)

        Phi_t = self.observer_intention(t)
        if Phi_t > 0.01:
            f += 0.5 * self.CHI_DELTA * Phi_t * self.recognition_filter(t) * Psi_real

        f += self.XI_AMP * (np.random.randn(self.N) + 1j * np.random.randn(self.N)) / np.sqrt(2)
        return f

    def step(self, t):
        # Strang Splitting: L(dt/2) -> NL(dt) -> L(dt/2)
        Psi_hat = fft(self.Psi)
        Psi_hat *= self.linear_half
        self.Psi = ifft(Psi_hat)

        Psi_hat_current = fft(self.Psi)
        dPsi = self.nonlinear_step(self.Psi, Psi_hat_current, t)
        self.Psi += self.dt * dPsi

        Psi_hat = fft(self.Psi)
        Psi_hat *= self.linear_half
        self.Psi = ifft(Psi_hat)

        return self.Psi

    def get_coherence(self):
        mean_Psi = np.mean(self.Psi)
        mean_rho = np.mean(np.abs(self.Psi) ** 2)
        if mean_rho < 1e-10:
            return 0.0
        return np.abs(mean_Psi) ** 2 / mean_rho

    def count_spin_nodes(self):
        rho = np.abs(self.Psi) ** 2
        above = rho > self.THRESHOLD_DK
        local_max = (rho > np.roll(rho, 1)) & (rho > np.roll(rho, -1))
        return int(np.sum(above & local_max))
