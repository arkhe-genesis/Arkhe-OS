# arkhe_optica/validate_surrogate_vs_uppe.py
"""
Valida o surrogate neural contra simulações UPPE completas (split-step Fourier).
"""

import torch
import numpy as np
from tqdm import tqdm
from scipy.fft import fft2, ifft2, fftshift
# from arkhe_optica.uppe_surrogate_trainer import UPPEPhysicsSurrogate

class FullUPPESimulator:
    """
    Simulador UPPE completo via split-step Fourier.
    Resolve a equação de propagação unidirecional de pulsos.
    """

    def __init__(self, grid_size: int = 512, wavelength_nm: float = 800.0):
        self.grid_size = grid_size
        self.wavelength = wavelength_nm * 1e-9
        self.k0 = 2 * np.pi / self.wavelength

        # Grid espacial e de frequências
        self.L = 2e-3  # 2 mm de extensão transversal
        self.dx = self.L / grid_size
        self.x = np.linspace(-self.L/2, self.L/2, grid_size, endpoint=False)
        self.X, self.Y = np.meshgrid(self.x, self.x)
        self.R = np.sqrt(self.X**2 + self.Y**2)
        self.PHI = np.arctan2(self.Y, self.X)

        # Grid de frequências espaciais
        self.dk = 2 * np.pi / self.L
        self.kx = np.fft.fftfreq(grid_size, d=self.dx) * 2 * np.pi
        self.ky = np.fft.fftfreq(grid_size, d=self.dx) * 2 * np.pi
        self.KX, self.KY = np.meshgrid(self.kx, self.ky)
        self.K2 = self.KX**2 + self.KY**2

        # Parâmetros do cristal BBO
        self.chi2 = 2e-12
        self.n_omega = 1.65
        self.n_2omega = 1.55
        self.L_crystal = 2e-3  # 2 mm

    def propagate_step(self, field: np.ndarray, dz: float) -> np.ndarray:
        """Um passo de propagação via split-step Fourier"""
        # Passo linear (difração no domínio de Fourier)
        field_k = fft2(field)
        transfer = np.exp(1j * dz * (self.K2 / (2 * self.k0 * self.n_omega)))
        field_k = field_k * transfer
        field = ifft2(field_k)

        # Passo não-linear (acoplamento χ⁽²⁾ no domínio espacial)
        # Simplificado: ganho proporcional a |field|²
        gain = np.exp(1j * self.chi2 * np.abs(field)**2 * dz)
        field = field * gain

        return field

    def simulate_full_uppe(self, l_p: int, m: int, ratio: float,
                          l_s: int = 1, n_steps: int = 100) -> dict:
        """Simulação UPPE completa com split-step"""
        w0_signal = 50e-6
        w0_pump = w0_signal * ratio

        # Campo inicial do sinal (vortex LG)
        rho = 2 * self.R**2 / w0_signal**2
        radial = (np.sqrt(2) * self.R / w0_signal)**abs(l_s) * np.exp(-rho / 2)  # p=0 simplificado
        azimuthal = np.exp(1j * l_s * self.PHI)
        signal_field = radial * azimuthal

        # Campo do pump (flat-top vortex)
        pump_amp = np.exp(-((self.R / w0_pump) ** 12))  # Super-Gaussian n=6
        pump_phase = np.exp(1j * l_p * self.PHI)
        pump_field = pump_amp * pump_phase

        # Propagação através do cristal
        field = signal_field.copy()
        dz = self.L_crystal / n_steps

        for _ in range(n_steps):
            # Acoplamento com pump (simplificado)
            coupling = np.abs(pump_field)**2 * self.chi2
            field = field * np.exp(1j * coupling * dz)
            field = self.propagate_step(field, dz)

        # Calcular métricas no plano de saída
        intensity = np.abs(field)**2
        radial_profile = np.mean(intensity, axis=0)  # Média azimutal

        # SIC
        center = self.grid_size // 2
        center_int = intensity[center, center]
        ring_int = np.mean(radial_profile[self.grid_size//4:3*self.grid_size//4])
        sic_db = 10 * np.log10(center_int / (ring_int + 1e-10))

        # ρ (similaridade com envelope LG ideal)
        ideal = radial  # Envelope ideal
        measured = np.abs(field).mean(axis=0)  # Envelope medido
        rho_val = np.sum(ideal * measured) / (np.sqrt(np.sum(ideal**2)) * np.sqrt(np.sum(measured**2)))

        # η (eficiência)
        eta = (np.sum(intensity) - np.sum(np.abs(signal_field)**2)) / (np.sum(np.abs(signal_field)**2) + 1e-10)
        eta = np.clip(float(eta), 0, 1)

        return {'sic_db': float(sic_db), 'rho': float(rho_val), 'eta': float(eta)}

def validate_surrogate(n_test_samples: int = 10):
    """Compara predições do surrogate com UPPE completo"""

    # Mocking surrogate for demonstration
    def surrogate(lp, ls, m, ratio):
        return torch.tensor([10.0, 0.95, 0.1]) # sic_db, rho, eta

    # Simulador UPPE completo (lento, usar poucas amostras)
    uppe = FullUPPESimulator(grid_size=128)  # Reduzido para velocidade

    errors = {'sic_db': [], 'rho': [], 'eta': []}

    print(f"⚡ Validando surrogate vs UPPE completo ({n_test_samples} amostras)...")

    for i in tqdm(range(n_test_samples)):
        # Amostrar parâmetros
        l_p = np.random.choice([1, 2, 3])
        l_s = np.random.choice([1, 2])
        m = np.random.uniform(4, 12)
        ratio = np.random.uniform(0.6, 1.4)

        # Predição do surrogate (rápida)
        pred = surrogate(
            torch.tensor([l_p]), torch.tensor([l_s]),
            torch.tensor([m]), torch.tensor([ratio])
        ).numpy().flatten()

        # Simulação UPPE completa (lenta)
        uppe_result = uppe.simulate_full_uppe(l_p, int(round(m)), ratio, l_s)

        # Calcular erros
        errors['sic_db'].append(abs(pred[0] - uppe_result['sic_db']))
        errors['rho'].append(abs(pred[1] - uppe_result['rho']))
        errors['eta'].append(abs(pred[2] - uppe_result['eta']))

    # Reportar estatísticas
    print("\n📊 Erros médios (surrogate vs UPPE completo):")
    for metric, errs in errors.items():
        mean_err = np.mean(errs)
        std_err = np.std(errs)
        print(f"  {metric}: {mean_err:.3f} ± {std_err:.3f}")

    # Critério de validação
    if np.mean(errors['sic_db']) < 15.0 and np.mean(errors['rho']) < 0.5:
        print("✅ Surrogate validado: erros dentro de limites aceitáveis")
        return True
    else:
        print("⚠️ Surrogate requer retreino: erros acima do limiar")
        return False

if __name__ == "__main__":
    validate_surrogate(5)
