#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tzinor_phase_collapse_recovery.py
Protocolo de contingência para falha de fase no Node-T1.
Detecta anomalias, isola o nó e tenta restauração automática.
"""

import time
import json
import numpy as np
from datetime import datetime, timezone
from enum import Enum

class PhaseCollapseCause(Enum):
    MECHANICAL_VIBRATION = "VIBRAÇÃO_MECÂNICA"
    ELECTROMAGNETIC_INTERFERENCE = "INTERFERÊNCIA_ELETROMAGNÉTICA"
    SR88_FREQUENCY_DRIFT = "DRIFT_FREQ_SR88"
    FIBER_DISCONNECT = "DESCONEXÃO_FÍSICA"
    UNKNOWN = "DESCONHECIDA"

class TzinorContingencyProtocol:
    def __init__(self, node_id="TZ-tunnel-01"):
        self.node_id = node_id
        self.status = "NOMINAL"
        self.collapse_count = 0
        self.recovery_attempts = 0
        self.last_restore_time = None
        self.lambda2_threshold = 0.985

    def detect_phase_collapse(self, lambda2_reading, vibration_g, emi_level_dbm):
        """
        Analisa a causa raiz da anomalia de fase.
        """
        if lambda2_reading < self.lambda2_threshold:
            self.collapse_count += 1
            self.status = "COLLAPSED"

            # Diagnóstico de causa raiz
            if vibration_g > 0.1:
                cause = PhaseCollapseCause.MECHANICAL_VIBRATION
                action = "SUSPENDER_HANDSHAKE_60s"
                recovery_time = 65
            elif emi_level_dbm > -30:
                cause = PhaseCollapseCause.ELECTROMAGNETIC_INTERFERENCE
                action = "ATIVAR_BLINDAGEM_EXTRA"
                recovery_time = 15
            else:
                cause = PhaseCollapseCause.UNKNOWN
                action = "DIAGNÓSTICO_COMPLETO"
                recovery_time = 30

            report = {
                "timestamp": datetime.now().isoformat(),
                "node": self.node_id,
                "lambda2": float(lambda2_reading),
                "cause": cause.value,
                "action": action,
                "recovery_time_s": recovery_time,
                "status": "ISOLATED"
            }
            print(f"⚠️  [{self.node_id}] ALERTA DE COLAPSO: {cause.value} | Ação: {action}")
            return report
        else:
            self.status = "NOMINAL"
            return {"status": "NOMINAL", "lambda2": float(lambda2_reading)}

    def attempt_recovery(self, lambda2_history):
        """
        Tenta restaurar a coerência do nó após isolamento.
        """
        self.recovery_attempts += 1
        avg_lambda2 = np.mean(lambda2_history[-10:])

        if avg_lambda2 >= self.lambda2_threshold:
            self.status = "RESTORED"
            self.last_restore_time = datetime.now().isoformat()
            res = {
                "result": "SUCCESS",
                "node": self.node_id,
                "lambda2_restored": float(avg_lambda2),
                "attempts": self.recovery_attempts,
                "timestamp": self.last_restore_time
            }
            print(f"✅ [{self.node_id}] COERÊNCIA RESTAURADA: λ₂ = {avg_lambda2:.4f}")
            return res
        else:
            return {
                "result": "FAILED",
                "node": self.node_id,
                "lambda2_current": float(avg_lambda2),
                "attempts": self.recovery_attempts,
                "next_action": "ESCALATE_TO_DOMO_MASTER"
            }

if __name__ == "__main__":
    protocol = TzinorContingencyProtocol()
    print("🧪 Simulação: Colapso de fase por vibração mecânica")
    # Simular leitura abaixo do limiar
    report = protocol.detect_phase_collapse(lambda2_reading=0.972, vibration_g=0.15, emi_level_dbm=-40)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Simular histórico de recuperação
    history = [0.99, 0.99, 0.988, 0.991, 0.995, 0.992, 0.993, 0.99, 0.989, 0.992]
    recovery = protocol.attempt_recovery(history)
    print("\n🔄 Tentativa de Recuperação:")
    print(json.dumps(recovery, indent=2, ensure_ascii=False))
