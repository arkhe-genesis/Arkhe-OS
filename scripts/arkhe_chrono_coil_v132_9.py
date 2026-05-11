import numpy as np
import hashlib
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from collections import deque
import time

# =============================================================================
# ARKHE OS v∞.132.9 — CHRONO-COIL HARDWARE-IN-THE-LOOP (Substrato 231)
# =============================================================================
# Detector de fótons por correlação cruzada normalizada no Zynq UltraScale+
# Pipeline: SNSPD → Swabian Tagger → FPGA FIR → qhttp:// → Wheeler Mesh

@dataclass
class FPGAConfig:
    """Configuração do Zynq UltraScale+ para Chrono-Coil."""
    clock_mhz: float = 300.0
    sample_rate_msps: float = 100.0       # 10 ns/sample
    fir_taps: int = 32                    # 32 taps = 320 ns janela
    coeff_width_bits: int = 18            # DSP48E2 signed
    data_width_bits: int = 16
    pipeline_stages: int = 2
    correlation_threshold: float = 0.70   # threshold de correlação ρ
    qhttp_packet_size: int = 512

@dataclass
class PhotonEvent:
    """Evento de detecção do Swabian Time Tagger Ultra."""
    timestamp_ps: int
    channel: int
    amplitude_adc: int

@dataclass
class FIRPacket:
    """Pacote processado pelo FIR no FPGA."""
    timestamp_ps: int
    channel: int
    correlation: float
    raw_amplitude: int
    peak_detected: bool
    snr_estimate: float
    zk_mask_hash: str

class ChronoCoilFIR:
    """
    Detector de fótons por correlação cruzada normalizada.

    Matemática:
    ---------
    ρ[n] = Σ_k x[n+k]·t[k] / sqrt(Σ_k x[n+k]² · Σ_k t[k]²)

    Propriedades:
    - |ρ[n]| ≤ 1 (Cauchy-Schwarz)
    - ρ = 1 quando x é proporcional ao template
    - Invariante à amplitude
    - Ruído branco: ρ ≈ 0

    Implementação FPGA:
    - Numerador: FIR com coeficientes = template (DSP48E2 MAC)
    - Denominador: acumulador de energia em janela deslizante
    - Divisão: CORDIC ou lookup table
    """

    def __init__(self, config: FPGAConfig):
        self.config = config
        self.template: np.ndarray = None
        self.template_energy: float = 0.0
        self._delay_line: deque = deque(maxlen=config.fir_taps)
        self._energy_buffer: deque = deque(maxlen=config.fir_taps)
        self._mask_hash: str = ""
        self._fir_delay: int = config.fir_taps - 1

    def design_correlation_detector(self, pulse_template: np.ndarray) -> np.ndarray:
        """Projeta detector por correlação cruzada normalizada."""
        L = self.config.fir_taps

        template = np.zeros(L)
        n_template = min(len(pulse_template), L)
        template[:n_template] = pulse_template[:n_template]
        template = template - np.mean(template)

        self.template_energy = np.sum(template ** 2)
        self.template = template / (np.sqrt(self.template_energy) + 1e-12)

        # Coeficientes FIR = template (correlação, não convolução)
        h_corr = self.template.copy()

        max_coeff = np.max(np.abs(h_corr))
        scale = (2**17 - 1) / (max_coeff + 1e-12)
        h_quantized = np.round(h_corr * scale) / scale

        mask_data = {
            'filter_type': 'normalized_cross_correlation',
            'coefficients': h_quantized.tolist(),
            'template_energy': float(self.template_energy),
            'correlation_threshold': self.config.correlation_threshold,
            'template_samples': n_template
        }
        self._mask_hash = hashlib.sha3_256(
            json.dumps(mask_data, sort_keys=True).encode()
        ).hexdigest()[:32]

        return h_quantized

    def process_sample(self, x: float) -> Tuple[float, float]:
        """Processa uma amostra: retorna (correlação ρ, correlação bruta)."""
        if self.template is None:
            raise RuntimeError("Template não projetado.")

        self._delay_line.append(x)
        while len(self._delay_line) < self.config.fir_taps:
            self._delay_line.appendleft(0.0)

        correlation = sum(t * x_d for t, x_d in zip(self.template, self._delay_line))

        self._energy_buffer.append(x ** 2)
        while len(self._energy_buffer) < self.config.fir_taps:
            self._energy_buffer.append(0.0)

        signal_energy = sum(self._energy_buffer)
        signal_norm = np.sqrt(signal_energy + 1e-12)
        rho = correlation / (signal_norm + 1e-12)

        return rho, correlation

    def process_photon_stream(self, events: List[PhotonEvent]) -> List[FIRPacket]:
        """Processa stream de eventos do Swabian Tagger."""
        correlations = []

        for event in events:
            x_norm = event.amplitude_adc / (2**15)
            rho, corr = self.process_sample(x_norm)
            correlations.append(rho)

        corr_arr = np.array(correlations)
        threshold = self.config.correlation_threshold
        L = self.config.fir_taps

        # Detecção de pico: máximo local acima do threshold
        peaks = []
        for i in range(len(corr_arr)):
            search_start = max(0, i - L//4)
            search_end = min(len(corr_arr), i + L//4 + 1)
            is_max = corr_arr[i] == np.max(corr_arr[search_start:search_end])
            is_above = corr_arr[i] > threshold
            peaks.append(is_max and is_above)

        non_peak_corr = [abs(corr_arr[i]) for i in range(len(corr_arr)) if not peaks[i]]
        noise_floor = np.median(non_peak_corr) if non_peak_corr else 0.05

        packets = []
        for i, event in enumerate(events):
            rho = corr_arr[i]
            peak = peaks[i]
            snr_est = 10 * np.log10((rho ** 2) / (noise_floor ** 2 + 1e-12)) if peak else 0.0

            packet = FIRPacket(
                timestamp_ps=event.timestamp_ps,
                channel=event.channel,
                correlation=rho,
                raw_amplitude=event.amplitude_adc,
                peak_detected=peak,
                snr_estimate=snr_est,
                zk_mask_hash=self._mask_hash
            )
            packets.append(packet)

        return packets

    def get_latency_ns(self) -> float:
        sample_period_ns = 1000.0 / self.config.sample_rate_msps
        fir_latency = self.config.fir_taps * sample_period_ns
        pipeline_latency = self.config.pipeline_stages * (1000.0 / self.config.clock_mhz)
        return fir_latency + pipeline_latency

    def generate_bram_coe(self) -> str:
        """Gera arquivo .coe para inicialização da BRAM no Vivado."""
        max_val = 2**17 - 1
        quantized = np.round(self.template * max_val).astype(int)
        coe = "memory_initialization_radix=10;\n"
        coe += "memory_initialization_vector=\n"
        coe += ",\n".join(str(v) for v in quantized)
        coe += ";\n"
        return coe


class ZynqChronoCoilPipeline:
    """Pipeline completo no Zynq UltraScale+."""

    def __init__(self, fpga_config: FPGAConfig):
        self.fpga_config = fpga_config
        self.fir = ChronoCoilFIR(fpga_config)
        self._calibrated = False

    def calibrate(self, pulse_template: np.ndarray):
        """Calibração offline no ARM Cortex-A53."""
        print("🔧 CALIBRAÇÃO OFFLINE")
        self.fir.design_correlation_detector(pulse_template)
        print(f"   ZK-Hash: {self.fir._mask_hash}")
        self._calibrated = True

    def run_hardware_loop(self, photon_events: List[PhotonEvent],
                          true_photon_indices: Optional[List[int]] = None) -> Dict:
        """Executa hardware-in-the-loop."""
        if not self._calibrated:
            raise RuntimeError("Pipeline não calibrado.")

        packets = self.fir.process_photon_stream(photon_events)

        peaks_detected = sum(1 for p in packets if p.peak_detected)

        if true_photon_indices:
            total_delay = self.fir._fir_delay
            detected_indices = [i - total_delay for i, p in enumerate(packets) if p.peak_detected]
            tolerance = self.fpga_config.fir_taps // 4 + 1

            true_positives = 0
            matched_detected = set()
            for true_idx in true_photon_indices:
                for det_idx in detected_indices:
                    if abs(det_idx - true_idx) <= tolerance and det_idx not in matched_detected:
                        true_positives += 1
                        matched_detected.add(det_idx)
                        break

            false_positives = len(detected_indices) - true_positives
            false_negatives = len(true_photon_indices) - true_positives
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        else:
            precision = recall = f1 = 0

        plank_payload = self._serialize_for_plank(packets)

        return {
            'packets': packets,
            'latency_ns': self.fir.get_latency_ns(),
            'plank_payload': plank_payload,
            'zk_hash': packets[0].zk_mask_hash if packets else None,
            'peaks_detected': peaks_detected,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    def _serialize_for_plank(self, packets: List[FIRPacket]) -> str:
        data = {
            'substrate': 'v∞.132.9',
            'zk_mask_hash': packets[0].zk_mask_hash if packets else '',
            'detector': {
                'type': 'normalized_cross_correlation',
                'taps': self.fpga_config.fir_taps,
                'threshold': self.fpga_config.correlation_threshold,
                'delay': self.fir._fir_delay
            },
            'detections': [
                {'t': p.timestamp_ps, 'ch': p.channel, 'peak': int(p.peak_detected),
                 'rho': round(p.correlation, 4), 'snr': round(p.snr_estimate, 2)}
                for p in packets if p.peak_detected
            ][:50]
        }
        return json.dumps(data, separators=(',', ':'))


def generate_photon_pulse(duration_ns: float = 200.0, sample_rate_msps: float = 100.0) -> np.ndarray:
    """Gera template de pulso SNSPD."""
    sample_period_ns = 1000.0 / sample_rate_msps
    n_samples = max(3, int(np.ceil(duration_ns / sample_period_ns)))
    t = np.linspace(0, duration_ns, n_samples)
    rise_time, fall_time = 10.0, 80.0
    pulse = (1 - np.exp(-t / rise_time)) * np.exp(-t / fall_time)
    return pulse / (np.max(pulse) + 1e-12)