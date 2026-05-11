#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tzinor_vibration_contingency.py
Protocolo de Contingência para Vibração Mecânica no Node-T1.
Ativa o modo 'Coerência de Espera' e o buffer de estado se a vibração > 0.1g.
"""

import numpy as np
import time
import json
import os

class VibrationContingencyManager:
    def __init__(self, node_id="Node-T1"):
        self.node_id = node_id
        self.vibration_threshold = 0.1 # g
        self.is_wait_mode = False
        self.buffer = []
        self.log = []

    def monitor_vibration(self, sensor_value):
        """Simula monitoramento de vibração via sensores MEMS"""
        if sensor_value > self.vibration_threshold:
            if not self.is_wait_mode:
                self.activate_wait_mode(sensor_value)
            return True
        else:
            if self.is_wait_mode:
                self.deactivate_wait_mode()
            return False

    def activate_wait_mode(self, intensity):
        self.is_wait_mode = True
        event = {
            "timestamp": time.strftime("%H:%M:%S"),
            "event": "COHERENCE_WAIT_MODE_ACTIVATED",
            "intensity": intensity,
            "action": "SUSPEND_HANDSHAKE_ACTIVATE_BUFFER"
        }
        self.log.append(event)
        print(f"🚨 [{event['timestamp']}] VIBRAÇÃO CRÍTICA ({intensity}g) DETECTADA no {self.node_id}!")
        print(f"🛡️ Ativando MODO DE ESPERA e BUFFER DE ESTADO.")

    def deactivate_wait_mode(self):
        self.is_wait_mode = False
        event = {
            "timestamp": time.strftime("%H:%M:%S"),
            "event": "COHERENCE_WAIT_MODE_DEACTIVATED",
            "action": "RESUME_HANDSHAKE_FLUSH_BUFFER"
        }
        self.log.append(event)
        print(f"✅ [{event['timestamp']}] Vibração estabilizada no {self.node_id}. Retomando handshake.")

    def run_simulation(self, duration_steps=10):
        print(f"🏗️ Iniciando Teste de Estresse de Vibração para {self.node_id}...")
        print("-" * 60)

        # Simular padrão de vibração (ex: trem passando)
        vibration_profile = [0.02, 0.05, 0.12, 0.15, 0.11, 0.08, 0.03, 0.01, 0.01, 0.01]

        for i, val in enumerate(vibration_profile):
            self.monitor_vibration(val)
            # Em modo de espera, a latência seria mantida via buffer (compensação de fase)
            status = "WAIT_MODE" if self.is_wait_mode else "NOMINAL"
            print(f"Passo {i+1:02d} | Vibração: {val:.2f}g | Status: {status}")
            time.sleep(0.5)

        # Salvar relatório
        output_path = "tzinor_vibration_contingency_report.json"
        with open(output_path, "w") as f:
            json.dump({
                "node": self.node_id,
                "threshold": self.vibration_threshold,
                "events": self.log
            }, f, indent=2)
        print("-" * 60)
        print(f"✅ Simulação de contingência concluída. Log: {output_path}")

if __name__ == "__main__":
    manager = VibrationContingencyManager()
    manager.run_simulation()
