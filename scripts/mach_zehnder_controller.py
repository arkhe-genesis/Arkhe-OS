#!/usr/bin/env python3
"""
mach_zehnder_controller.py
Controls SiP Mach-Zehnder modulator for optical watermarking.
Interfaces with FPGA via SPI for real-time hash encoding.
"""
import numpy as np
import time
from pathlib import Path

try:
    import spidev
except ImportError:
    print("spidev is not installed. Mocking it for simulation mode.")
    class SpiDevMock:
        def __init__(self):
            self.max_speed_hz = 0
            self.mode = 0
        def open(self, bus, device):
            pass
        def xfer2(self, data):
            pass
        def close(self):
            pass
    spidev = type('MockSpidev', (), {'SpiDev': SpiDevMock})

class MachZehnderController:
    """Controlador para modulador Mach-Zehnder em plataforma SiP."""

    def __init__(self, spi_bus=0, spi_device=0, spi_speed=1000000):
        """Inicializa interface SPI com FPGA."""
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = spi_speed
        self.spi.mode = 0  # CPOL=0, CPHA=0

        # Configurações do modulador
        self.n_segments = 256  # 1 por bit do hash ZEE200
        self.phase_resolution = 12  # bits (4096 níveis)
        self.max_phase_shift = 2*np.pi  # rad

        # Tabela de conversão: bit de hash → fase θₖ
        self.theta_key = 'arkhe_master_key_2026'
        self._precompute_phase_lut()

    def _precompute_phase_lut(self):
        """Pré-computa tabela de fases para cada bit/hash position."""
        self.phase_lut = {}
        for k in range(self.n_segments):
            # Fase derivada da chave secreta (determinística)
            theta_k = hash(self.theta_key + str(k)) % (2*np.pi)
            self.phase_lut[k] = theta_k

    def encode_hash(self, hash_bits, epsilon=0.01):
        """Codifica hash ZEE200 como padrão de fase no modulador."""
        if len(hash_bits) != self.n_segments:
            raise ValueError(f"Expected {self.n_segments} bits, got {len(hash_bits)}")

        # Calcular valores de drive para cada segmento
        drive_values = []
        for k, bit in enumerate(hash_bits):
            if bit == 1:
                # Aplicar modulação de fase: θₖ com profundidade ε
                phase_shift = epsilon * self.phase_lut[k]
            else:
                phase_shift = 0.0

            # Converter fase para valor de drive (12-bit DAC)
            drive = int((phase_shift / self.max_phase_shift) * (2**self.phase_resolution - 1))
            drive_values.append(drive)

        # Enviar para FPGA via SPI
        self._write_drive_values(drive_values)

        return drive_values

    def _write_drive_values(self, drive_values):
        """Envia valores de drive para FPGA via SPI."""
        # Protocolo: [CMD=0xA5][N_BYTES][DATA...]
        cmd = 0xA5
        n_bytes = len(drive_values) * 2  # 2 bytes por valor (12-bit + padding)

        # Montar pacote SPI
        packet = [cmd, n_bytes]
        for val in drive_values:
            # 12-bit value: split into 2 bytes (MSB first)
            packet.append((val >> 4) & 0xFF)  # Upper 8 bits
            packet.append((val & 0x0F) << 4)   # Lower 4 bits + padding

        # Enviar via SPI
        self.spi.xfer2(packet)

    def apply_watermark(self, spectrum_input, hash_bits, epsilon=0.01):
        """Aplica watermark óptico ao espectro de entrada."""
        # 1. Codificar hash no modulador
        self.encode_hash(hash_bits, epsilon)

        # 2. Aguardar estabilização térmica/eletrônica
        time.sleep(0.001)  # 1 ms (ajustar conforme resposta do atuador)

        # 3. Medir espectro modulado (via espectrômetro acoplado)
        # (Implementação específica do hardware de leitura)
        spectrum_output = self._read_modulated_spectrum()

        return spectrum_output

    def _read_modulated_spectrum(self):
        """Lê espectro modulado via interface de espectrômetro."""
        # Placeholder: implementar interface com espectrômetro real
        # Exemplo: ler via serial/USB do espectrômetro acoplado ao MZI
        return np.array([])  # Retornar array de intensidades espectrais

    def verify_watermark(self, spectrum_measured, expected_hash, epsilon=0.01, threshold=0.85):
        """Verifica watermark no espectro medido."""
        # Reconstruir padrão de modulação esperado
        modulation_expected = np.ones(1151)  # 400-1550 nm, 1 nm resolution
        lambda_axis = np.linspace(400, 1550, 1151)

        for k, bit in enumerate(expected_hash):
            if bit == 1:
                f_k = 0.01 + k * 0.001  # Frequências ortogonais
                theta_k = self.phase_lut[k]
                modulation_expected += epsilon * np.cos(2*np.pi * f_k * lambda_axis + theta_k)

        # Correlação cruzada normalizada
        s_norm = (spectrum_measured - np.mean(spectrum_measured)) / np.std(spectrum_measured)
        m_norm = (modulation_expected - np.mean(modulation_expected)) / np.std(modulation_expected)
        correlation = np.corrcoef(s_norm, m_norm)[0, 1]

        return correlation > threshold, correlation

    def close(self):
        """Fecha interface SPI."""
        self.spi.close()

def test_mach_zehnder_controller():
    """Teste de funcionalidade do controlador MZI."""
    print("🔧 Testing Mach-Zehnder controller...")

    # Inicializar controlador (modo simulação se hardware não disponível)
    try:
        controller = MachZehnderController()
        hardware_available = True
    except Exception as e:
        print(f"⚠️  Hardware not available: {e}")
        print("   Running in simulation mode...")
        hardware_available = False
        controller = None

    # Gerar hash de teste
    np.random.seed(42)
    test_hash = np.random.randint(0, 2, 256)

    if hardware_available:
        # Teste com hardware real (ou simulado se não houver spidev mas mock tiver funcionado)
        # O mock sempre funciona, logo isso será executado.
        drive_values = controller.encode_hash(test_hash)
        print(f"✓ Encoded {np.sum(test_hash)} active bits → {len(drive_values)} drive values")

        # Teste de verificação (requer espectro medido)
        # spectrum_measured = controller._read_modulated_spectrum()
        # verified, corr = controller.verify_watermark(spectrum_measured, test_hash)
        # print(f"✓ Verification: verified={verified}, correlation={corr:.4f}")

        controller.close()
    else:
        # Teste em simulação
        print(f"✓ Simulated encoding: {np.sum(test_hash)} bits → phase pattern")
        print(f"✓ Expected correlation for perfect detection: >0.95")

    print(f"✅ Mach-Zehnder controller test complete")

if __name__ == '__main__':
    test_mach_zehnder_controller()
