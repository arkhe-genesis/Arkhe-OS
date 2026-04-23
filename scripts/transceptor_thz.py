#!/usr/bin/env python3
import numpy as np
import json
import sys

class TransceptorGNR:
    """
    Pilar 4: Barramento THz (Akyildiz & Jornet)
    Modelagem do canal intra-chip (0.5 - 2.5 THz)
    """
    def __init__(self, freq_central=2.5e12, pulso_ps=0.1):
        self.freq = freq_central
        self.pulso = pulso_ps * 1e-12
        self.c = 3e8

    def calcular_path_loss(self, distancia_mm=1.0):
        # Modelo simplificado de Akyildiz 2010
        d = distancia_mm * 1e-3
        # Free space loss
        loss_fs = 20 * np.log10(4 * np.pi * self.freq * d / self.c)
        # Molecular absorption (approx for 1mm in 2.5 THz)
        loss_abs = 5.0 * (self.freq / 1e12) * d * 1000
        return loss_fs + loss_abs

    def simular_transmissao(self, bits, d_mm=1.0):
        pl = self.calcular_path_loss(d_mm)
        snr = 60.0 - pl / 10.0 # Heurística baseada no survey

        # BER para TS-OOK / PPM
        if snr > 15:
            ber = 1e-6
        elif snr > 5:
            ber = 1e-3
        else:
            ber = 0.1

        erros = np.random.random(len(bits)) < ber
        bits_recebidos = np.logical_xor(bits, erros).astype(int)

        return {
            "bits_enviados": len(bits),
            "distancia_mm": d_mm,
            "path_loss_db": float(pl),
            "snr_db": float(snr),
            "ber_estimado": float(ber),
            "sucesso": bool(ber < 1e-2)
        }

def main():
    try:
        tx = TransceptorGNR()
        teste_bits = [1, 0, 1, 1, 0, 0, 1, 0]
        resultado = tx.simular_transmissao(teste_bits, d_mm=1.0)

        print(json.dumps({
            "substrate": "37-Pilar4",
            "name": "THz Bus (GNR Antenna)",
            "telemetry": resultado,
            "verdict": "VOICE_RESONANT" if resultado["sucesso"] else "SIGNAL_DECAY"
        }, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
