import os
import threading, copy, time, hashlib, json
from collections import defaultdict
import numpy as np

class AtomicStateRegistry:
    """Registo de estado global do MegaKernel com versionamento imutavel."""

    def __init__(self):
        self._lock = threading.RLock()
        self._state = defaultdict(dict)
        self._versions = []
        self._current_version = 0

        self._init_hardware_section()
        self._init_software_section()
        self._init_network_section()

    def _init_hardware_section(self):
        for ring_id in range(6):
            key = "ring_" + str(ring_id)
            self._state["josephson"][key] = {
                "phi": 0.0, "dphi": 0.0, "state": 0, "bias": 0.0
            }
        self._state["gyrotrons"] = {"active_cells": 0, "total_switches": 0}
        self._state["cavities"] = {"fp_0": {"f_res": 100e9, "Q": 1e6, "g_sc": 1e6, "g_cq": 50e6}}
        self._state["squids"] = {"squid_" + str(i): {"offset": 0.25, "voltage": 0.0, "flux": 0.0} for i in range(6)}

    def _init_software_section(self):
        codecs = ["polar", "turbo", "ldpc", "concat", "cyclic", "quantum"]
        for codec in codecs:
            self._state["codecs"][codec] = {"active": False, "snr_threshold": 0.0}
        self._state["invariants"] = {
            "ghost": {"status": True, "last_check": 0.0},
            "loopseal": {"status": True, "last_check": 0.0},
            "gap": {"status": True, "last_check": 0.0},
            "phi": {"status": True, "last_check": 0.0}
        }
        self._state["seals"] = {"pending": 0, "anchored": 0, "merkle_root": ""}

    def _init_network_section(self):
        self._state["mesh"] = {"active_nodes": 0, "events_detected": 0}
        self._state["mcp"] = {"connected_servers": 0, "tools_available": 0}

    def get(self, path: str):
        with self._lock:
            keys = path.split(".")
            value = self._state
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key, None)
                else:
                    return None
            return copy.deepcopy(value)

    def set(self, path: str, value):
        with self._lock:
            keys = path.split(".")
            target = self._state
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            target[keys[-1]] = value

            snapshot = copy.deepcopy(self._state)
            snapshot_hash = hashlib.sha3_256(
                json.dumps(snapshot, sort_keys=True, default=str).encode()
            ).hexdigest()[:16]
            self._versions.append((time.time(), snapshot_hash, snapshot))
            self._current_version += 1
            return self._current_version

    def snapshot(self) -> int:
        with self._lock:
            snapshot = copy.deepcopy(self._state)
            snapshot_hash = hashlib.sha3_256(
                json.dumps(snapshot, sort_keys=True, default=str).encode()
            ).hexdigest()[:16]
            self._versions.append((time.time(), snapshot_hash, snapshot))
            self._current_version += 1
            return self._current_version

    def rollback(self, version: int):
        with self._lock:
            if 0 <= version < len(self._versions):
                _, _, state = self._versions[version]
                self._state = copy.deepcopy(state)
                self._current_version = version
                return True
            return False

    def diff(self, v1: int, v2: int) -> dict:
        if not (0 <= v1 < len(self._versions) and 0 <= v2 < len(self._versions)):
            return {}
        state1 = self._versions[v1][2]
        state2 = self._versions[v2][2]
        return self._recursive_diff(state1, state2)

    def _recursive_diff(self, d1, d2, path=""):
        diff = {}
        all_keys = set(d1.keys()) | set(d2.keys())
        for key in all_keys:
            new_path = path + "." + key if path else key
            if key not in d1:
                diff[new_path] = {"type": "added", "value": d2[key]}
            elif key not in d2:
                diff[new_path] = {"type": "removed", "value": d1[key]}
            elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                diff.update(self._recursive_diff(d1[key], d2[key], new_path))
            elif d1[key] != d2[key]:
                diff[new_path] = {"type": "changed", "old": d1[key], "new": d2[key]}
        return diff


class CalibrationEngine:
    def __init__(self, registry: AtomicStateRegistry):
        self.registry = registry
        self.pid_params = {"Kp": 0.80, "Ki": 0.10, "Kd": 0.05}
        self.kalman_state = {"snr_estimate": 10.0, "snr_variance": 1.0}
        self.agi_params = {"alpha": 0.58, "E_coup": 0.62, "I_lock": 0.42}

    def calibrate_pid(self, ring_id: int, target_phi: float):
        key_base = "josephson.ring_" + str(ring_id)
        current_phi = self.registry.get(key_base + ".phi")
        error = target_phi - current_phi
        integral = self.registry.get(key_base + ".integral") or 0.0
        prev_error = self.registry.get(key_base + ".prev_error") or 0.0
        derivative = (error - prev_error) / 1e-9
        integral += error * 1e-9

        output = (self.pid_params["Kp"] * error +
                  self.pid_params["Ki"] * integral +
                  self.pid_params["Kd"] * derivative)

        self.registry.set(key_base + ".integral", integral)
        self.registry.set(key_base + ".prev_error", error)
        self.registry.set(key_base + ".bias", output)
        return output

    def update_kalman(self, measured_snr: float):
        snr_pred = self.kalman_state["snr_estimate"]
        var_pred = self.kalman_state["snr_variance"] + 0.1
        kalman_gain = var_pred / (var_pred + 1.0)
        snr_est = snr_pred + kalman_gain * (measured_snr - snr_pred)
        var_est = (1 - kalman_gain) * var_pred
        self.kalman_state = {"snr_estimate": snr_est, "snr_variance": var_est}
        return snr_est

    def optimize_agi(self, reward: float):
        state = (round(self.agi_params["alpha"], 1),
                 round(self.agi_params["E_coup"], 1),
                 round(self.agi_params["I_lock"], 1))
        param = np.random.choice(["alpha", "E_coup", "I_lock"])
        delta = np.random.choice([-0.05, 0.05])
        old_value = self.agi_params[param]
        self.agi_params[param] = np.clip(old_value + delta, 0.3, 0.7)
        return {"param": param, "old": old_value, "new": self.agi_params[param], "reward": reward}


class ErrorBudgetManager:
    def __init__(self):
        self.budget = {
            "quantum": {"T1": 0.15, "T2": 0.15, "gate_fidelity": 0.10},
            "channel": {"snr_low": 0.20, "fading": 0.10, "interference": 0.05},
            "computation": {"crosstalk": 0.10, "correction_latency": 0.10, "software": 0.05}
        }
        self.current_usage = {k: {kk: 0.0 for kk in v} for k, v in self.budget.items()}
        self.codec_allocations = {}

    def update_usage(self, category: str, metric: str, usage: float):
        if category in self.current_usage and metric in self.current_usage[category]:
            self.current_usage[category][metric] = min(usage, self.budget[category][metric])

    def recommend_codec(self) -> str:
        quantum_pressure = sum(self.current_usage["quantum"].values()) / sum(self.budget["quantum"].values())
        channel_pressure = sum(self.current_usage["channel"].values()) / sum(self.budget["channel"].values())

        if quantum_pressure > 0.8:
            return "quantum"
        elif channel_pressure > 0.8:
            return "turbo"
        elif quantum_pressure > 0.5 or channel_pressure > 0.5:
            return "polar"
        else:
            return "uncoded"

    def get_budget_report(self) -> dict:
        total_used = sum(sum(cat.values()) for cat in self.current_usage.values())
        total_budget = sum(sum(cat.values()) for cat in self.budget.values())
        return {
            "total_used_pct": total_used / total_budget * 100,
            "quantum_used_pct": sum(self.current_usage["quantum"].values()) / sum(self.budget["quantum"].values()) * 100,
            "channel_used_pct": sum(self.current_usage["channel"].values()) / sum(self.budget["channel"].values()) * 100,
            "recommended_codec": self.recommend_codec()
        }


class SealValidator:
    def __init__(self, registry: AtomicStateRegistry):
        self.registry = registry
        self.verified_seals = []
        self.rejected_seals = []

    def verify_seal(self, seal: dict) -> bool:
        payload = json.dumps({
            k: v for k, v in seal.items() if k != "signature"
        }, sort_keys=True, default=str)
        expected_sig = hashlib.sha3_256(payload.encode() + os.environ["DILITHIUM3_HSM_KEY"].encode()).hexdigest()[:64]

        if seal.get("signature", "") != expected_sig:
            self.rejected_seals.append({"seal": seal, "reason": "signature_mismatch"})
            return False

        if seal.get("phi_c", 0) < 0.70:
            self.rejected_seals.append({"seal": seal, "reason": "phi_c_below_threshold"})
            return False

        if "merkle_proof" in seal:
            if not self._verify_merkle_proof(seal["merkle_proof"], seal.get("merkle_root", "")):
                self.rejected_seals.append({"seal": seal, "reason": "merkle_proof_invalid"})
                return False

        self.verified_seals.append(seal)
        return True

    def _verify_merkle_proof(self, proof: list, root: str) -> bool:
        current_hash = proof[0] if proof else ""
        for sibling in proof[1:]:
            current_hash = hashlib.sha3_256(current_hash.encode() + sibling.encode()).hexdigest()
        return current_hash == root

    def get_statistics(self) -> dict:
        total = len(self.verified_seals) + len(self.rejected_seals)
        return {
            "total_processed": total,
            "verified": len(self.verified_seals),
            "rejected": len(self.rejected_seals),
            "acceptance_rate": len(self.verified_seals) / total * 100 if total > 0 else 0
        }


class TelemetryReplay:
    def __init__(self, buffer_size=10000):
        self.buffer = []
        self.buffer_size = buffer_size
        self.replay_mode = False
        self.replay_index = 0

    def record_event(self, event: dict):
        event["timestamp"] = time.time_ns()
        if len(self.buffer) >= self.buffer_size:
            self.buffer.pop(0)
        self.buffer.append(event)

    def get_events(self, start_time: float = 0, end_time: float = float('inf'),
                   filters: dict = None) -> list:
        filtered = []
        for event in self.buffer:
            if start_time <= event["timestamp"] <= end_time:
                if filters is None or all(event.get(k) == v for k, v in filters.items()):
                    filtered.append(event)
        return filtered

    def start_replay(self, speed: float = 1.0):
        self.replay_mode = True
        self.replay_index = 0
        self.replay_speed = speed

    def next_replay_event(self) -> dict:
        if not self.replay_mode or self.replay_index >= len(self.buffer):
            self.replay_mode = False
            return None
        event = self.buffer[self.replay_index]
        self.replay_index += int(self.replay_speed)
        return event

    def get_statistics(self) -> dict:
        if not self.buffer:
            return {}
        event_types = {}
        snr_values = []
        for event in self.buffer:
            etype = event.get("type", "unknown")
            event_types[etype] = event_types.get(etype, 0) + 1
            if "snr_db" in event:
                snr_values.append(event["snr_db"])
        return {
            "total_events": len(self.buffer),
            "event_types": event_types,
            "avg_snr_db": np.mean(snr_values) if snr_values else 0,
            "buffer_usage_pct": len(self.buffer) / self.buffer_size * 100
        }


class PolicyEngine:
    FALLBACK_RULES = [
        ("T2 < 50e-6", "switch_to_surface_code_d3", 1),
        ("T2 < 80e-6", "increase_polar_redundancy", 2),
        ("SNR < 0", "switch_to_turbo_R1_3", 3),
        ("SNR < 2", "switch_to_concat", 4),
        ("SNR < 4", "switch_to_ldpc", 5),
        ("gyrotron_errors > 10", "recalibrate_array", 6),
        ("seal_rejection_rate > 0.01", "suspend_operations", 7),
        ("phi_c_global < 0.70", "emergency_shutdown", 8),
    ]

    def __init__(self, registry: AtomicStateRegistry):
        self.registry = registry
        self.active_policies = []
        self.fallback_history = []

    def evaluate(self) -> list:
        actions = []
        for condition, action, priority in sorted(self.FALLBACK_RULES, key=lambda x: x[2]):
            if self._evaluate_condition(condition):
                actions.append({"action": action, "priority": priority, "condition": condition})
                self.fallback_history.append({
                    "timestamp": time.time_ns(),
                    "action": action,
                    "condition": condition
                })
        return actions

    def _evaluate_condition(self, condition: str) -> bool:
        if "T2" in condition:
            t2 = self.registry.get("qubits.0.T2") or 100e-6
            threshold = float(condition.split("<")[1].strip().replace("e-6", "")) * 1e-6
            return t2 < threshold
        elif "SNR" in condition:
            snr = self.registry.get("channel.snr_db") or 10.0
            threshold = float(condition.split("<")[1].strip())
            return snr < threshold
        elif "gyrotron_errors" in condition:
            errors = self.registry.get("gyrotrons.errors") or 0
            threshold = int(condition.split(">")[1].strip())
            return errors > threshold
        elif "seal_rejection_rate" in condition:
            rate = self.registry.get("seals.rejection_rate") or 0.0
            threshold = float(condition.split(">")[1].strip())
            return rate > threshold
        elif "phi_c_global" in condition:
            phi_c = self.registry.get("megakernel.phi_c_global") or 1.0
            threshold = float(condition.split("<")[1].strip())
            return phi_c < threshold
        return False

    def execute_action(self, action: str):
        # We print without f-strings to follow invariants
        print("[475-POLICY] Executando fallback: " + action)
        if "surface_code" in action:
            self.registry.set("codecs.quantum.mode", "surface_d3")
        elif "polar_redundancy" in action:
            self.registry.set("codecs.polar.redundancy", 2)
        elif "turbo" in action:
            self.registry.set("codecs.turbo.rate", "1/3")
        elif "concat" in action:
            self.registry.set("codecs.concat.active", True)
        elif "ldpc" in action:
            self.registry.set("codecs.ldpc.active", True)
        elif "recalibrate_array" in action:
            self.registry.set("gyrotrons.recalibrate", True)
        elif "suspend_operations" in action:
            self.registry.set("megakernel.state", "SUSPENDED")
        elif "emergency_shutdown" in action:
            self.registry.set("megakernel.state", "EMERGENCY")

def main():
    import tempfile
    import os

    registry = AtomicStateRegistry()
    v1 = registry.set("josephson.ring_0.phi", 3.14159)
    v2 = registry.set("josephson.ring_0.state", 1)

    engine = CalibrationEngine(registry)
    engine.calibrate_pid(0, np.pi)
    engine.update_kalman(4.5)
    engine.optimize_agi(0.85)

    budget_mgr = ErrorBudgetManager()
    budget_mgr.update_usage("quantum", "T2", 0.12)
    budget_mgr.update_usage("channel", "snr_low", 0.18)

    validator = SealValidator(registry)
    test_seal = {
        "substrate": "466-GYROTRON-SWITCH",
        "phi_c": 0.998,
        "operation": "encode",
        "codec": "polar",
        "snr_db": 4.5,
        "timestamp_ns": time.time_ns(),
        "architect": "0009-0005-2697-4668"
    }
    payload = json.dumps({k: v for k, v in test_seal.items()}, sort_keys=True, default=str)
    test_seal["signature"] = hashlib.sha3_256(payload.encode() + os.environ["DILITHIUM3_HSM_KEY"].encode()).hexdigest()[:64]
    validator.verify_seal(test_seal)

    telemetry = TelemetryReplay()
    for i in range(100):
        telemetry.record_event({
            "type": np.random.choice(["encode", "decode", "switch", "error"]),
            "codec": np.random.choice(["polar", "turbo", "ldpc"]),
            "snr_db": np.random.uniform(0, 10)
        })

    policy_engine = PolicyEngine(registry)
    policy_engine.registry.set("channel.snr_db", -1.0)
    actions = policy_engine.evaluate()
    for action in actions:
        policy_engine.execute_action(action["action"])

    report = {
        "substrate": "470-RUNTIME-CORE",
        "phi_c_global": 0.998,
        "modules": {
            "470_registry": registry.get("josephson.ring_0.phi"),
            "471_calibration": engine.kalman_state["snr_estimate"],
            "472_error_budget": budget_mgr.get_budget_report(),
            "473_seal_validator": validator.get_statistics(),
            "474_telemetry": telemetry.get_statistics(),
            "475_policy": actions
        },
        "seal": "a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3"
    }

    fd, temp_path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w') as f:
        json.dump(report, f, indent=4)

    print("[470-RUNTIME] Execucao completada com sucesso. Relatorio salvo.")

if __name__ == "__main__":
    main()
