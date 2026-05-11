# metalens_v4_interface.py
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
# import serial # Removido para simulação básica

@dataclass
class MetalensConfig:
    """Configuração da Metalens V4.0"""
    wavelength: float = 633e-9  # 633 nm (vermelho HeNe)
    numerical_aperture: float = 0.95
    focal_length: float = 50e-6  # 50 μm
    pixel_size: float = 250e-9  # 250 nm (TiO₂ nanofins)
    array_size: Tuple[int, int] = (512, 512)
    phase_range: float = 2 * np.pi

class MetalensV4:
    """
    Interface de leitura/escrita para Metalens V4.0
    Usada para modulação de fase e amplitude do feixe
    que interage com o cristal ressonante.
    """

    def __init__(self, config: MetalensConfig = None, port: str = '/dev/ttyACM0'):
        self.config = config or MetalensConfig()
        # self.serial = serial.Serial(port, 115200, timeout=1)
        self.phase_map = np.zeros(self.config.array_size, dtype=np.float32)
        self.amplitude_map = np.ones(self.config.array_size, dtype=np.float32)

    def write_phase(self, phase_value: float, region: Optional[Tuple[int, int, int, int]] = None):
        """
        Escreve um padrão de fase na metalens.
        """
        if region:
            x1, y1, x2, y2 = region
            self.phase_map[y1:y2, x1:x2] = phase_value
        else:
            self.phase_map[:] = phase_value

        # self._send_commands(self._phase_to_nanofin_commands(self.phase_map))

    def read_phase(self) -> float:
        """
        Lê a fase atual do feixe refletido pelo cristal.
        """
        # Simulação: retorna a fase média atual + algum ruído
        return np.mean(self.phase_map) + np.random.normal(0, 0.01)

    def encode_intention(self, intention_hash: bytes, coherence_m: float) -> np.ndarray:
        """
        Codifica uma intenção e coerência em um padrão holográfico
        na metalens para gravação no cristal.
        """
        x = np.linspace(-1, 1, self.config.array_size[0])
        y = np.linspace(-1, 1, self.config.array_size[1])
        X, Y = np.meshgrid(x, y)

        hash_seed = int.from_bytes(intention_hash[:4], 'big')
        np.random.seed(hash_seed)
        random_phase = np.random.rand(*self.config.array_size) * 2 * np.pi

        coherence_mod = coherence_m * np.exp(-(X**2 + Y**2) / (2 * 0.5**2))

        hologram = random_phase * coherence_mod
        return hologram

    def _phase_to_nanofin_commands(self, phase_map: np.ndarray) -> bytes:
        quantized = np.round(phase_map / (2 * np.pi) * 15).astype(np.uint8)
        commands = bytearray()
        commands.extend(b'WRITE_PHASE')
        commands.extend(quantized.tobytes())
        return bytes(commands)

    def _send_commands(self, commands: bytes):
        # self.serial.write(commands + b'\n')
        pass
