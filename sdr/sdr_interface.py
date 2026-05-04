import numpy as np
import subprocess
import json
from typing import Optional, Dict, Tuple

class SDRInterface:
    """
    Interface de Rádio Definido por Software.
    Suporta RTL-SDR, USRP B2xx, HackRF via bibliotecas externas ou CLI.
    """
    def __init__(self, device: str = "rtl", frequency_mhz: float = 915.0,
                 sample_rate_msps: float = 2.4, gain_db: float = 40.0):
        self.device = device
        self.frequency = frequency_mhz * 1e6
        self.sample_rate = sample_rate_msps * 1e6
        self.gain = gain_db
        self._driver = None

    def initialize(self) -> bool:
        """Inicializa o hardware SDR."""
        try:
            if self.device == "rtl":
                # Verifica se rtl_power está disponível
                subprocess.run(["rtl_power", "--help"], capture_output=True, check=True)
            elif self.device == "usrp":
                import uhd
                self._driver = uhd.usrp.MultiUSRP()
            elif self.device == "hackrf":
                subprocess.run(["hackrf_info"], capture_output=True, check=True)
            print(f"✅ SDR {self.device} inicializado em {self.frequency/1e6:.1f} MHz")
            return True
        except Exception as e:
            print(f"❌ Falha ao inicializar SDR: {e}")
            return False

    def measure_rssi(self, duration_s: float = 1.0) -> float:
        """Mede a potência média recebida (RSSI) em dBm."""
        try:
            # Usa rtl_power para medir potência (exemplo genérico)
            result = subprocess.run(
                ["rtl_power", "-f", f"{self.frequency/1e6:.0f}M:{self.frequency/1e6+2:.0f}M:1M",
                 "-g", str(int(self.gain)), "-i", str(int(duration_s)), "-1"],
                capture_output=True, text=True, timeout=10
            )
            # Parseia saída (exemplo: "2024-01-01, 915.0, 917.0, 1.0, -45.2")
            lines = result.stdout.strip().split('\n')
            powers = [float(line.split(',')[-1].strip()) for line in lines if line]
            return np.mean(powers) if powers else -100.0
        except:
            return -100.0

    def estimate_channels(self, num_devices: int) -> np.ndarray:
        """Estima coeficientes de canal via medição de RSSI por dispositivo."""
        # Em produção: usar pilotos OFDM ou sweeping de frequência
        # Aqui, simula baseado em RSSI medido
        rssi = self.measure_rssi()
        # Converte RSSI para ganho de canal (escala Rayleigh)
        scale = 10 ** (rssi / 20) * 0.1
        return np.random.rayleigh(scale=scale, size=(num_devices, 12))

    def transmit_allocation(self, power_matrix: np.ndarray):
        """Transmite a matriz de alocação de potência para os dispositivos IoT."""
        # Serializa e envia via downlink (ex: broadcast LoRa ou NBIoT)
        payload = json.dumps(power_matrix.tolist())
        print(f"📡 Transmitindo alocação de potência para {power_matrix.shape[0]} dispositivos...")
        # Em produção: usar o rádio para enviar payload
        return True

# Integração no UnifiedOrchestrator
# Isso seria inserido no seu código existente que define UnifiedOrchestrator
# Aqui é apenas um mock para a estrutura.
class UnifiedOrchestratorWithSDR:
    def __init__(self, config: dict):
        self.config = config
        self.sdr = None
        if config.get("sdr", {}).get("enabled", False):
            self.sdr = SDRInterface(
                device=config["sdr"].get("device", "rtl"),
                frequency_mhz=config["sdr"].get("frequency_mhz", 915.0),
                sample_rate_msps=config["sdr"].get("sample_rate_msps", 2.4),
                gain_db=config["sdr"].get("gain_db", 40.0)
            )
            self.sdr.initialize()

    def optimize_6g_power_realtime(self, num_devices: int = 24, use_sdr_channels: bool = True):
        """Executa MOGA com canais medidos em tempo real via SDR."""
        from substrates.v168_6g_noma_power_manifold import NOMAManifold
        from monte_carlo_noma_6g import SimulationConfig, MOGAOptimizer

        config = SimulationConfig(total_iot_devices=num_devices)
        manifold = NOMAManifold(config)

        # Obtém canais reais (ou simulados)
        if use_sdr_channels and self.sdr:
            channels = self.sdr.estimate_channels(num_devices)
        else:
            channels = manifold.generate_channels()

        moga = MOGAOptimizer(manifold, pop_size=50, generations=150)
        best_power, best_fitness = moga.optimize(channels)

        # Transmite alocação via SDR
        if self.sdr:
            self.sdr.transmit_allocation(best_power)

        return best_power, best_fitness, channels
