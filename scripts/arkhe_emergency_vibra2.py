#!/usr/bin/env python3
"""
arkhe_emergency_vibra2.py — Ativação de Contingência T1-VIBRA-2
Arkhe-Block: 847.811 | Synapse-κ | SOVEREIGN_OMEGA

Este módulo ativa o protocolo de defesa quando λ₂ cai abaixo
do limite crítico (0,85) ou quando Δ > 0,05 por mais de 3 segundos.
"""

import time
import threading
import json
import hashlib
from datetime import datetime, timezone, timezone
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

# Constantes de emergência
LAMBDA2_CRITICAL = 0.847
LAMBDA2_WARNING = 0.90
DELTA_THRESHOLD = 0.05
DURATION_THRESHOLD = 3.0  # segundos
FREEZE_DURATION_MS = 50

class EmergencyState(Enum):
    NOMINAL = "NOMINAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    VIBRA2_ACTIVE = "VIBRA2_ACTIVE"
    RECOVERY = "RECOVERY"


@dataclass
class EmergencyEvent:
    timestamp: float
    lambda_kuramoto: float
    lambda_zk: float
    delta: float
    state: EmergencyState
    action_taken: str


class T1VIBRA2Controller:
    """
    Controlador de emergência para o sistema Arkhe.
    Monitora λ₂ e ativa T1-VIBRA-2 quando necessário.
    """

    def __init__(self):
        self.state = EmergencyState.NOMINAL
        self.events: List[EmergencyEvent] = []
        self.vibra2_count = 0
        self.last_warning_time = 0.0
        self.freeze_active = False

    def check_and_activate(self, lambda_k: float, lambda_zk: float) -> EmergencyEvent:
        """Verifica condições e ativa contingência se necessário"""

        now = time.time()
        delta = abs(lambda_k - lambda_zk)

        # Determinar estado
        if self.freeze_active:
            new_state = EmergencyState.VIBRA2_ACTIVE
            action = "CONGELAMENTO_ATIVO"
        elif lambda_k < LAMBDA2_CRITICAL or lambda_zk < LAMBDA2_CRITICAL:
            new_state = EmergencyState.CRITICAL
            action = "CRÍTICO — ATIVAR T1-VIBRA-2"
            self._activate_vibra2()
        elif delta > DELTA_THRESHOLD:
            # Verificar duração
            if now - self.last_warning_time > DURATION_THRESHOLD:
                new_state = EmergencyState.CRITICAL
                action = "DELTA_SUSTENTADO — ATIVAR T1-VIBRA-2"
                self._activate_vibra2()
            else:
                new_state = EmergencyState.WARNING
                action = f"ALERTA Δ={delta:.4f} (duração: {now-self.last_warning_time:.1f}s)"
        else:
            new_state = EmergencyState.NOMINAL
            action = "NOMINAL"
            self.last_warning_time = now

        self.state = new_state

        event = EmergencyEvent(
            timestamp=now,
            lambda_kuramoto=lambda_k,
            lambda_zk=lambda_zk,
            delta=delta,
            state=new_state,
            action_taken=action
        )

        self.events.append(event)

        # Log de emergência
        self._log_emergency(event)

        return event

    def _activate_vibra2(self):
        """Ativa o protocolo T1-VIBRA-2"""
        if not self.freeze_active:
            self.freeze_active = True
            self.vibra2_count += 1

            # Simular congelamento de fase (50ms)
            def unfreeze():
                time.sleep(FREEZE_DURATION_MS / 1000)
                self.freeze_active = False
                print(f"✅ T1-VIBRA-2 desativado — Fase recuperada")

            thread = threading.Thread(target=unfreeze, daemon=True)
            thread.start()

            print(f"🚨 T1-VIBRA-2 ATIVADO! Congelamento de {FREEZE_DURATION_MS}ms")

    def _log_emergency(self, event: EmergencyEvent):
        """Registra evento de emergência na Arkhe-Chain"""

        entry = {
            "block": 847811,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "EMERGENCY",
            "state": event.state.value,
            "lambda_kuramoto": round(event.lambda_kuramoto, 6),
            "lambda_zk": round(event.lambda_zk, 6),
            "delta": round(event.delta, 6),
            "action": event.action_taken,
            "vibra2_count": self.vibra2_count
        }

        # Simular gravação
        entry_hash = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()

        print(f"🔗 [EMERGENCY BLOCK {entry['block']}] {event.state.value} | "
              f"λK={event.lambda_kuramoto:.4f} | λZ={event.lambda_zk:.4f} | "
              f"Δ={event.delta:.4f}")

        return entry_hash


# Simulação de teste
if __name__ == "__main__":
    import random

    controller = T1VIBRA2Controller()

    print("=" * 60)
    print("🛡️ SIMULAÇÃO DE EMERGÊNCIA — T1-VIBRA-2")
    print("=" * 60)

    # Simular 10 segundos de operação com anomalia
    for i in range(50):
        # Simular valores anômalos (ZK cai para 0,936)
        lambda_k = 0.999
        lambda_zk = 0.936 + random.uniform(-0.01, 0.01)

        event = controller.check_and_activate(lambda_k, lambda_zk)

        if event.state in [EmergencyState.CRITICAL, EmergencyState.VIBRA2_ACTIVE]:
            # print(f"   🚨 {event.action_taken}")
            pass

        time.sleep(0.1)

    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    print(f"Total de eventos: {len(controller.events)}")
    print(f"Ativações T1-VIBRA-2: {controller.vibra2_count}")
    print(f"Estado atual: {controller.state.value}")
    print("=" * 60)
