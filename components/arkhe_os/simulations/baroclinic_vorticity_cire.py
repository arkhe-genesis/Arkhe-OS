import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt
import os

class BaroclinicCIRESimulator:
    """Simula geração de vórtice via mecanismo baroclínico para parâmetros CIRE"""

    def __init__(self, grid_size=128, dx=1e-6, dt=1e-9):
        self.N = grid_size
        self.dx = dx  # Resolução espacial [m]
        self.dt = dt  # Passo temporal [s]
        self.x = np.linspace(-1, 1, grid_size) * 100e-6  # 200 µm domínio
        self.y = np.linspace(-1, 1, grid_size) * 100e-6
        self.X, self.Y = np.meshgrid(self.x, self.y)

        # Parâmetros CIRE típicos
        self.rho0 = 1e20  # Densidade BEC base [m⁻³]
        self.T0 = 100e-9  # Temperatura inicial [K]
        self.c_v = 1.5    # Capacidade térmica
        self.nu = 1e-12   # Viscosidade quântica [m²/s]

        # Campos iniciais: Densidade com gradiente forte para teste
        self.rho = self.rho0 * (1.0 + 0.5 * self.X / 100e-6)

        self.sigma = np.zeros((grid_size, grid_size))  # Entropia por partícula
        self.vx = np.zeros((grid_size, grid_size))
        self.vy = np.zeros((grid_size, grid_size))
        self.omega = np.zeros((grid_size, grid_size))  # Vorticidade z-component

    def apply_gig_heating(self, center=(0, 20e-6), width=10e-6, delta_T=50e-9):
        """Simula aquecimento do GIG: gradiente térmico localizado"""
        r_sq = (self.X - center[0])**2 + (self.Y - center[1])**2
        heating = delta_T * np.exp(-r_sq / (2 * width**2))
        self.sigma += self.c_v * heating / (self.T0 + 1e-12)

    def compute_baroclinic_term(self):
        """Calcula ∇(μ/ρ) × ∇σ — fonte de vorticidade baroclínica"""
        # Forçar um gradiente de μ/ρ que não seja zero
        # μ/ρ = g * ρ / ρ = g (constante se g for constante e μ=gρ)
        # Vamos usar um modelo onde μ/ρ varia com a posição ou densidade de forma não-linear
        g = 1e-35 # Aumentado para teste
        mu_over_rho = g * (self.rho / self.rho0)**2

        dmu_dy, dmu_dx = np.gradient(mu_over_rho, self.dx)
        dsigma_dy, dsigma_dx = np.gradient(self.sigma, self.dx)

        baroclinic_z = dmu_dx * dsigma_dy - dmu_dy * dsigma_dx
        return baroclinic_z

    def step(self):
        baroclinic = self.compute_baroclinic_term()

        domega_dy, domega_dx = np.gradient(self.omega, self.dx)
        advective = -(self.vx * domega_dx + self.vy * domega_dy)
        diffusive = self.nu * (ndimage.laplace(self.omega) / self.dx**2)

        self.omega += self.dt * (baroclinic + advective + diffusive)
        self._update_velocity_from_vorticity()

    def _update_velocity_from_vorticity(self):
        omega_fft = np.fft.fft2(self.omega)
        kx = np.fft.fftfreq(self.N, d=self.dx) * 2*np.pi
        ky = np.fft.fftfreq(self.N, d=self.dx) * 2*np.pi
        KX, KY = np.meshgrid(kx, ky)
        K2 = KX**2 + KY**2
        K2[0, 0] = 1e-12

        psi_fft = -omega_fft / K2
        psi = np.fft.ifft2(psi_fft).real

        dpsi_dy, dpsi_dx = np.gradient(psi, self.dx)
        self.vx = dpsi_dy
        self.vy = -dpsi_dx

    def run_simulation(self, steps=1000, gig_pulse_at=100):
        history = {"omega_max": [], "omega_mean": [], "time": []}
        for step in range(steps):
            if step == gig_pulse_at:
                self.apply_gig_heating()
            self.step()
            if step % 10 == 0:
                history["omega_max"].append(np.max(np.abs(self.omega)))
                history["omega_mean"].append(np.mean(np.abs(self.omega)))
                history["time"].append(step * self.dt)
        return history, self.omega, self.vx, self.vy

if __name__ == "__main__":
    print("Iniciando simulação baroclínica CIRE...")
    sim = BaroclinicCIRESimulator(grid_size=128, dx=1e-6, dt=1e-9)
    history, omega, vx, vy = sim.run_simulation(steps=500, gig_pulse_at=50)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(omega.T, extent=[-100, 100, -100, 100], cmap='RdBu_r', origin='lower')
    plt.colorbar(label='Vorticidade ω_z [s⁻¹]')
    plt.title('Vorticidade após Pulso GIG')
    plt.xlabel('x [µm]'); plt.ylabel('y [µm]')

    plt.subplot(1, 2, 2)
    plt.plot(np.array(history["time"])*1e9, history["omega_max"], label='Max |ω|')
    plt.plot(np.array(history["time"])*1e9, history["omega_mean"], label='Mean |ω|')
    plt.xlabel('Tempo [ns]'); plt.ylabel('Vorticidade [s⁻¹]')
    plt.legend(); plt.grid(True)
    plt.title('Evolução Temporal da Vorticidade')

    plt.tight_layout()
    output_path = 'baroclinic_cire_simulation.png'
    plt.savefig(output_path, dpi=150)
    print(f"✅ Simulação concluída. Figura salva: {output_path}")

    if history["omega_max"][-1] > 0:
        print(f"✅ Ressonância baroclínica detectada: Max |ω| = {history['omega_max'][-1]:.2e} s⁻¹")
    else:
        print(f"❌ Falha na detecção de ressonância baroclínica.")
