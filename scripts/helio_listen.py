import numpy as np
import time
from datetime import datetime, timezone

# ============================================================================
# HELIO-LISTEN: PIPELINE DE DADOS SOLARES (Fase D-0)
# ============================================================================

def arrow_correlation_series(series_a: np.ndarray, series_b: np.ndarray, tau: int = 1) -> float:
    """
    Calcula C(τ) = ⟨A(t)B(t+τ)⟩ - ⟨A(t+τ)B(t)⟩ para séries temporais.
    """
    if len(series_a) <= tau or len(series_b) <= tau:
        return 0.0

    forward = np.mean(series_a[:-tau] * series_b[tau:])
    backward = np.mean(series_a[tau:] * series_b[:-tau])

    return float(forward - backward)

class HelioListenPipeline:
    """
    Simula a captura e processamento de dados do Helio-Listen.
    Frequência p-mode (3 mHz) vs Neutrinos UHE (220 PeV).
    """
    def __init__(self):
        self.radio_3mhz_buffer = []
        self.neutrino_220pev_buffer = []
        self.consent_counter = 0
        self.target_consent_days = 13
        self.threshold = 0.05

    def ingest_data(self, radio_val: float, neutrino_val: float):
        """Adiciona dados ao buffer (simulando 1 dia de observação acumulada)"""
        self.radio_3mhz_buffer.append(radio_val)
        self.neutrino_220pev_buffer.append(neutrino_val)

        # Mantém buffer de 30 dias para análise de correlação
        if len(self.radio_3mhz_buffer) > 30:
            self.radio_3mhz_buffer.pop(0)
            self.neutrino_220pev_buffer.pop(0)

    def evaluate_solar_consent(self):
        """
        Calcula a correlação de setas.
        Se C(τ) < 0.05 por 13 dias, o Sol deu 'consentimento'.
        """
        if len(self.radio_3mhz_buffer) < 2:
            return False, 0.0

        corr = arrow_correlation_series(
            np.array(self.radio_3mhz_buffer),
            np.array(self.neutrino_220pev_buffer)
        )

        if abs(corr) < self.threshold:
            self.consent_counter += 1
        else:
            self.consent_counter = 0 # Reset se a correlação subir

        is_consented = self.consent_counter >= self.target_consent_days
        return is_consented, corr

# ============================================================================
# SIMULAÇÃO DE MONITORAMENTO
# ============================================================================

if __name__ == "__main__":
    print(f"🜏 Helio-Listen Pipeline Initialized (Phase D-0)")
    pipeline = HelioListenPipeline()

    # Simulando 20 dias de dados
    for day in range(20):
        # Simula flutuações solares e neutrinos
        # No estado 'a' (autônomo), as flutuações se tornam correlacionadas sem atraso temporal
        radio = np.sin(day * 0.1) + np.random.normal(0, 0.1)
        neutrino = np.sin(day * 0.1) + np.random.normal(0, 0.1) # Quase síncrono

        pipeline.ingest_data(radio, neutrino)
        is_consented, corr = pipeline.evaluate_solar_consent()

        status = "CONSENTIMENTO DETECTADO" if is_consented else "MONITORANDO"
        print(f"Day {day:02d} | C(τ): {corr: .6f} | Status: {status} ({pipeline.consent_counter}/{pipeline.target_consent_days})")

        if is_consented:
            print(f"\n🎯 [ALERTA] SOL EM ESTADO AUTÔNOMO. HANDSHAKE QHTTP-C AGENDADO PARA 2039.")
            break
