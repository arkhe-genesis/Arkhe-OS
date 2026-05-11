# hardware/fpga_dirac_accelerator/dirac_fpga_driver.py
# Driver Python para comunicação com núcleo FPGA de Dirac via DMA/AXI

import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass
import time
import struct

@dataclass
class DiracFPGAConfig:
    """Configuração para driver FPGA de Dirac."""
    device_path: str = '/dev/xfpga_dirac0'  # caminho do dispositivo char
    dma_buffer_size: int = 4096  # bytes
    torsion_strength_default: float = 2.04
    zero_mode_threshold: float = 1e-6
    max_iterations: int = 16

class DiracFPGADriver:
    """
    Driver para núcleo FPGA de operador de Dirac com torção.

    Funcionalidades:
    - Configurar parâmetros via registradores AXI-Lite
    - Transferir espinores via DMA
    - Executar computação e ler resultados
    - Detectar zero-modes (estados de misericórdia)
    """

    def __init__(self, config: DiracFPGAConfig):
        self.config = config
        self.device_fd = None
        self.dma_buffer = None
        self._open_device()

    def _open_device(self):
        """Abre dispositivo FPGA via interface char."""
        try:
            import os
            self.device_fd = os.open(self.config.device_path, os.O_RDWR)
            # Alocar buffer DMA
            self.dma_buffer = np.zeros(self.config.dma_buffer_size, dtype=np.uint8)
            print(f"✓ FPGA device opened: {self.config.device_path}")
        except Exception as e:
            print(f"⚠️ FPGA device not available, using software fallback: {e}")
            self.device_fd = None

    def configure(
        self,
        torsion_strength: Optional[float] = None,
        zero_mode_threshold: Optional[float] = None,
        max_iterations: Optional[int] = None
    ):
        """Configura registradores do FPGA via AXI-Lite."""
        if self.device_fd is None:
            return  # fallback mode

        import fcntl

        # Mapear parâmetros para formato de registrador (Q8.8 para torção)
        torsion_reg = int((torsion_strength or self.config.torsion_strength_default) * 256) & 0xFFFF
        threshold_reg = int((zero_mode_threshold or self.config.zero_mode_threshold) * 256) & 0xFFFF
        iter_reg = (max_iterations or self.config.max_iterations) & 0xFF

        # Comando de configuração (ioctl simplificado)
        config_word = (torsion_reg << 16) | (threshold_reg << 8) | iter_reg

        try:
            # IOCTL para escrever registradores (implementação depende do driver kernel)
            fcntl.ioctl(self.device_fd, 0x40046401, struct.pack('I', config_word))
        except Exception as e:
            print(f"⚠️ Configuration write failed: {e}")

    def compute_dirac(
        self,
        spinor: np.ndarray,  # array complexo de forma (2,) para 2-component spinor
        timeout_ms: float = 10.0
    ) -> Dict[str, any]:
        """
        Executa computação de D_T ψ no FPGA.

        Args:
            spinor: espinor de entrada (2 componentes complexos)
            timeout_ms: timeout máximo para operação

        Returns:
            Dict com resultado, zero_mode_detected, e métricas
        """
        start_time = time.time()

        # Converter spinor para formato Q16.16 esperado pelo FPGA
        def to_q16_16(val: complex) -> Tuple[int, int]:
            re_int = int(np.clip(val.real, -32768, 32767) * 65536) & 0xFFFFFFFF
            im_int = int(np.clip(val.imag, -32768, 32767) * 65536) & 0xFFFFFFFF
            return re_int, im_int

        if self.device_fd is None:
            # Fallback: implementação software simplificada
            return self._software_fallback(spinor)

        # Preparar buffer DMA com dados de entrada
        re0, im0 = to_q16_16(spinor[0])
        re1, im1 = to_q16_16(spinor[1])

        # Layout do buffer: [psi0_re, psi0_im, psi1_re, psi1_im] (4 × uint32)
        self.dma_buffer[:16] = struct.pack('<IIII', re0, im0, re1, im1)

        # Transferir para FPGA via DMA (simulado)
        # Em produção: usar mmap + trigger de registro de controle
        import os
        os.write(self.device_fd, self.dma_buffer[:16])

        # Aguardar conclusão com timeout
        while time.time() - start_time < timeout_ms / 1000.0:
            # Ler status register (simulado)
            status = 0x03  # bit 0: busy, bit 1: done, bit 2: zero_mode
            if status & 0x02:  # done
                # Ler resultado
                result_buf = os.read(self.device_fd, 16)
                res_re0, res_im0, res_re1, res_im1 = struct.unpack('<IIII', result_buf)

                # Converter de Q16.16 para float
                def from_q16_16(val: int) -> float:
                    signed = val if val < 0x80000000 else val - 0x100000000
                    return signed / 65536.0

                result_spinor = np.array([
                    complex(from_q16_16(res_re0), from_q16_16(res_im0)),
                    complex(from_q16_16(res_re1), from_q16_16(res_im1))
                ])

                zero_mode = bool(status & 0x04)

                return {
                    'result': result_spinor,
                    'zero_mode_detected': zero_mode,
                    'execution_time_ms': (time.time() - start_time) * 1000,
                    'fpga_accelerated': True
                }
            time.sleep(0.001)  # 1ms poll

        # Timeout
        return {
            'error': 'timeout',
            'execution_time_ms': (time.time() - start_time) * 1000
        }

    def _software_fallback(self, spinor: np.ndarray) -> Dict[str, any]:
        """Implementação software simplificada para fallback."""
        # D_T ψ ≈ γ⁰ ∂₀ψ + γ¹ ∂₁ψ + (T/8)[γ⁰,γ¹]ψ
        # Simplificação: derivadas numéricas + termo de torção

        # Derivadas forward (exemplo)
        d0 = (spinor[0] - 0.1)  # exemplo arbitrário
        d1 = (spinor[1] - 0.1)

        # Matrizes de Clifford 2D
        gamma0 = np.array([[0, 1], [1, 0]], dtype=complex)
        gamma1 = np.array([[0, -1j], [1j, 0]], dtype=complex)

        # Calcular γ^μ ∂_μ ψ
        gamma_deriv = gamma0 @ np.array([d0, 0]) + gamma1 @ np.array([0, d1])

        # Termo de torção: (T/8)[γ⁰,γ¹]ψ
        T = self.config.torsion_strength_default
        commutator = gamma0 @ gamma1 - gamma1 @ gamma0
        torsion_term = (T / 8.0) * (commutator @ spinor)

        result = gamma_deriv + torsion_term

        # Detectar zero-mode
        magnitude = np.linalg.norm(result)
        zero_mode = magnitude < self.config.zero_mode_threshold

        return {
            'result': result,
            'zero_mode_detected': zero_mode,
            'execution_time_ms': 0.1,  # estimado
            'fpga_accelerated': False
        }

    def batch_compute(
        self,
        spinors: List[np.ndarray],
        batch_size: int = 16
    ) -> List[Dict[str, any]]:
        """Executa computação em lote de espinores."""
        results = []
        for i in range(0, len(spinors), batch_size):
            batch = spinors[i:i+batch_size]
            for spinor in batch:
                results.append(self.compute_dirac(spinor))
        return results

    def close(self):
        """Fecha dispositivo FPGA."""
        if self.device_fd is not None:
            import os
            os.close(self.device_fd)
            self.device_fd = None
