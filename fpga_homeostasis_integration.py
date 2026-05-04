#!/usr/bin/env python3
"""
fpga_homeostasis_integration.py
Integrates FPGA PI controller with optical homeostasis loop.
"""
import numpy as np
import time
import json
from pathlib import Path

class FPGAHomeostasisController:
    """Interface com controlador PI em FPGA para homeostase óptica."""

    def __init__(self, fpga_config_path='config/fpga_pi_config.json'):
        """Inicializa comunicação com FPGA."""
        # Mocking config creation for execution if it doesn't exist
        if not Path(fpga_config_path).exists():
            Path(fpga_config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(fpga_config_path, 'w') as f:
                json.dump({
                    "gain_prop": 32,
                    "gain_int": 0,
                    "kappa_min": 0.1,
                    "kappa_max": 2.0
                }, f)

        # Carregar configuração de ganhos do FPGA
        with open(fpga_config_path, 'r') as f:
            self.config = json.load(f)

        self.gamma_prop = self.config['gain_prop']  # Q1.15 fixed-point
        self.gamma_int = self.config['gain_int']
        self.kappa_min = self.config['kappa_min']
        self.kappa_max = self.config['kappa_max']

        # Buffer espectral para cálculo de erro
        self.target_spectrum = None  # Carregar de arquivo de referência
        self.spectral_buffer = np.zeros(1151)  # 400-1550 nm, 1 nm resolution

    def load_target_spectrum(self, filepath='reference/capture_spectrum.npy'):
        """Carrega espectro alvo para regime CAPTURE."""
        if not Path(filepath).exists():
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            np.save(filepath, np.ones(1151))

        self.target_spectrum = np.load(filepath)
        print(f"✓ Loaded target spectrum: {filepath}")

    def compute_spectral_error(self, measured_spectrum):
        """Calcula erro espectral δ = ∫|S(λ) - S_target(λ)|² dλ."""
        if self.target_spectrum is None:
            raise ValueError("Target spectrum not loaded")

        # Erro quadrático médio espectral
        error = np.trapezoid((measured_spectrum - self.target_spectrum)**2, dx=1.0)  # 1 nm resolution
        return float(error)

    def send_error_to_fpga(self, error_value):
        """Envia valor de erro para FPGA via interface SPI/UART."""
        # Converter erro para formato fixo esperado pelo FPGA
        # Exemplo: Q1.31 fixed-point para erro espectral
        error_fixed = int(np.clip(error_value * (2**31), -2**31, 2**31-1))

        # Enviar via interface serial (simulado aqui)
        # Em produção: usar pyserial para comunicação com FPGA
        # print(f"   → Sent error to FPGA: {error_value:.2e} (fixed: {error_fixed})")

        return True

    def read_kappa_from_fpga(self):
        """Lê valor de κ ajustado do FPGA."""
        # Simular leitura do FPGA (em produção: ler via SPI/UART)
        # Retornar κ em formato float para uso no loop óptico
        kappa_fixed = 12288  # Exemplo: κ = 0.75 em Q1.15
        kappa_float = kappa_fixed / (2**15)  # Converter Q1.15 → float

        return kappa_float

    def run_homeostasis_loop(self, spectral_measurement_fn, max_iterations=1000):
        """Executa loop homeostático com FPGA no controle."""
        print(f"🔄 Starting optical homeostasis loop with FPGA controller...")

        kappa_history = []
        error_history = []
        coherence_history = []

        for iteration in range(max_iterations):
            # 1. Medir espectro atual (via espectrômetro acoplado)
            measured_spectrum = spectral_measurement_fn()

            # 2. Calcular erro espectral
            error = self.compute_spectral_error(measured_spectrum)
            error_history.append(error)

            # 3. Enviar erro para FPGA
            self.send_error_to_fpga(error)

            # 4. Ler κ ajustado do FPGA
            kappa = self.read_kappa_from_fpga()
            kappa_history.append(kappa)

            # 5. Aplicar κ ao sistema óptico (via atuador Kerr/termo-óptico)
            self._apply_kappa_to_optical_system(kappa)

            # 6. Calcular coerência (para monitoramento)
            coherence = self._estimate_coherence(measured_spectrum)
            coherence_history.append(coherence)

            # 7. Verificar convergência
            if error < 1e-4 and iteration > 100:
                print(f"✓ Converged at iteration {iteration}: error={error:.2e}, κ={kappa:.4f}")
                break

            # Log periódico
            if iteration % 100 == 0:
                print(f"   Iter {iteration:4d}: error={error:.2e}, κ={kappa:.4f}, coh={coherence:.4f}")

        return {
            'kappa_history': kappa_history,
            'error_history': error_history,
            'coherence_history': coherence_history,
            'converged': error < 1e-4,
            'final_kappa': kappa,
            'final_error': error
        }

    def _apply_kappa_to_optical_system(self, kappa):
        """Aplica valor de κ ao sistema óptico (atuador Kerr/termo-óptico)."""
        # Implementação específica do hardware atuador
        # Exemplo: enviar código DAC para driver do atuador
        # print(f"   → Applied κ = {kappa:.4f} to optical actuator")
        pass

    def _estimate_coherence(self, spectrum):
        """Estima coerência a partir do espectro medido."""
        # Métrica simplificada: razão pico/largura do espectro
        peak = np.max(spectrum)
        fwhm = self._compute_fwhm(spectrum)
        coherence = peak / (fwhm + 1e-6)  # Evitar divisão por zero
        return min(1.0, coherence / 10.0)  # Normalizar para [0, 1]

    def _compute_fwhm(self, spectrum):
        """Computa largura a meia altura (FWHM) do espectro."""
        peak = np.max(spectrum)
        half_max = peak / 2
        indices = np.where(spectrum >= half_max)[0]
        if len(indices) < 2:
            return 1151  # Full width if no clear peak
        return indices[-1] - indices[0]  # Width in nm (1 nm resolution)

def test_fpga_integration():
    """Teste de integração do controlador FPGA."""
    print("🧠 Testing FPGA homeostasis integration...")

    # Inicializar controlador
    controller = FPGAHomeostasisController()
    controller.load_target_spectrum()

    # Função de medição espectral simulada
    def mock_spectral_measurement():
        # Simular espectro com ruído próximo ao alvo
        base = controller.target_spectrum
        noise = np.random.normal(0, 0.01, len(base))
        return np.clip(base + noise, 0, None)

    # Executar loop homeostático (simulado)
    results = controller.run_homeostasis_loop(mock_spectral_measurement, max_iterations=500)

    print(f"✓ Loop complete: converged={results['converged']}")
    print(f"✓ Final κ: {results['final_kappa']:.4f}")
    print(f"✓ Final error: {results['final_error']:.2e}")

    # Salvar histórico para análise
    Path('results/fpga_integration').mkdir(parents=True, exist_ok=True)
    np.savez('results/fpga_integration/homeostasis_log.npz', **results)

    print(f"💾 Results saved: results/fpga_integration/homeostasis_log.npz")
    print(f"✅ FPGA integration test complete")

if __name__ == '__main__':
    test_fpga_integration()
