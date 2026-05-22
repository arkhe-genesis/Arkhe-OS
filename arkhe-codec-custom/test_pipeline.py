#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tempfile
import json
import sys
import os

# Ensure import of codec_engine
sys.path.append(os.path.dirname(__file__))
from codec_engine import CustomAdaptiveCodec

class MockKernelTest:
    def __init__(self):
        self.state = {
            "neel_angle_rad": 0.012,
            "cavity_freq_ghz": 100.0,
            "system_coherence_phi_c": 0.9912,
            "telemetry": {"current_ber": 2.1e-5}
        }

    def get(self, path, default=None):
        if path == "telemetry":
            return self.state["telemetry"]
        if path == "system_coherence_phi_c":
            return self.state["system_coherence_phi_c"]
        if path == "telemetry.current_ber":
            return self.state["telemetry"].get("current_ber", default)
        return default

if __name__ == "__main__":
    # 1. Inicializa o plugin customizado gerado pelo SDK
    meu_codec = CustomAdaptiveCodec()
    kernel_instance = MockKernelTest()

    # 2. Simula execucao com ruido baixo (Espera-se taxa de codificacao alta 0.75)
    kernel_instance.state["telemetry"]["current_ber"] = 1e-7
    report_limpo = meu_codec.execute_pipeline(kernel_instance)
    print("[TESTE SDK] Canal limpo -> Acao do Codec: " + report_limpo["action"] + " | Taxa alocada: " + str(report_limpo["allocated_code_rate"]))

    # 3. Simula execucao sob estresse termico severo (Espera-se taxa de codificacao protetiva 0.33)
    kernel_instance.state["telemetry"]["current_ber"] = 5e-4
    report_ruido = meu_codec.execute_pipeline(kernel_instance)
    print("[TESTE SDK] Canal ruidoso -> Acao do Codec: " + report_ruido["action"] + " | Taxa alocada: " + str(report_ruido["allocated_code_rate"]))

    # Output temporary canon seal
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w') as f:
        json.dump({
            "status": "SUCCESS",
            "clean_channel_action": report_limpo["action"],
            "clean_channel_rate": report_limpo["allocated_code_rate"],
            "noisy_channel_action": report_ruido["action"],
            "noisy_channel_rate": report_ruido["allocated_code_rate"]
        }, f)
    print("Test pipeline sealed output at: " + path)
