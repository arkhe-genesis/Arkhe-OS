#!/usr/bin/env python3
"""
ARKHE OS — SOAR Integration
Substrato 394: Resposta automática a eventos críticos (desligamento, alarme, trigger externo)
"""
import hashlib
import json
import time

class SOARSystem:
    def __init__(self):
        self.rules = {
            "CRITICAL_TEMP": self._action_shutdown,
            "HIGH_RADIATION": self._action_alarm,
            "UNAUTHORIZED_ACCESS": self._action_lockdown,
            "PRIMAKOFF_TRIGGER": self._action_external_trigger
        }
        self.actions_taken = []

    def process_event(self, event_type: str, details: dict):
        action_func = self.rules.get(event_type)
        if action_func:
            return action_func(details)
        return {"status": "IGNORED", "event": event_type}

    def _action_shutdown(self, details):
        action = {"action": "SHUTDOWN", "reason": "Temperature exceeded limit", "time": time.time()}
        self.actions_taken.append(action)
        return action

    def _action_alarm(self, details):
        action = {"action": "ALARM", "level": details.get("level", "HIGH"), "time": time.time()}
        self.actions_taken.append(action)
        return action

    def _action_lockdown(self, details):
        action = {"action": "LOCKDOWN", "location": details.get("location", "UNKNOWN"), "time": time.time()}
        self.actions_taken.append(action)
        return action

    def _action_external_trigger(self, details):
        action = {"action": "EXTERNAL_TRIGGER", "target": "PRIMAKOFF_DAQ", "time": time.time()}
        self.actions_taken.append(action)
        return action

def generate_seal(actions):
    record = {
        "substrate": "394-SOAR",
        "actions_count": len(actions),
        "timestamp": time.time(),
        "status": "CANONIZED"
    }
    return hashlib.sha3_256(json.dumps(record, sort_keys=True).encode()).hexdigest()

def main():
    soar = SOARSystem()
    print("=" * 70)
    print("ARKHE OS — SOAR INTEGRATION (Substrato 394)")
    print("=" * 70)

    events = [
        ("CRITICAL_TEMP", {"temp": 85.5}),
        ("HIGH_RADIATION", {"level": "CRITICAL", "value": 1500}),
        ("PRIMAKOFF_TRIGGER", {"confidence": 0.99})
    ]

    for evt_type, evt_details in events:
        res = soar.process_event(evt_type, evt_details)
        print(f"Evento: {evt_type} -> Ação: {res['action']}")

    seal = generate_seal(soar.actions_taken)
    print(f"\nSelo Canônico: {seal}")

if __name__ == "__main__":
    main()
