#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import time
import sys
import os

# Referencia em memoria simulando a conexao direta ao Kernel do ARKHE OS
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'arkhe-codec-custom'))
from codec_engine import CustomAdaptiveCodec

app = Flask("ArkheAgiBridge")

class MockKernel:
    def __init__(self):
        self.state = {
            "neel_angle_rad": 0.012,
            "cavity_freq_ghz": 100.0,
            "system_coherence_phi_c": 0.9912,
            "telemetry": {"current_ber": 2.1e-5}
        }
        self.active_fallback_tier = "L0_NORMAL"

    def mutate_state(self, path, value):
        self.state[path] = value
        return True

kernel_instance = MockKernel()

@app.route("/v1/state", methods=["GET"])
def get_arkhe_state():
    """
    Rota utilizada pelo LangGraph para ler as variaveis de estado
    do hardware antes de executar ramificacoes no grafo de decisao.
    """
    return jsonify({
        "status": "SUCCESS",
        "timestamp_ns": time.time_ns(),
        "payload": kernel_instance.state,
        "fallback_tier": kernel_instance.active_fallback_tier
    }), 200

@app.route("/v1/calibrate", methods=["POST"])
def post_agi_calibration():
    """
    Rota para agentes do AutoGen ajustarem os pesos de acoplamento
    do motor de calibracao fina com base em analises historicas.
    """
    data = request.json or {}
    target_param = data.get("parameter")
    new_value = data.get("value")

    if target_param in ["cavity_freq_ghz", "neel_angle_rad"]:
        kernel_instance.mutate_state(target_param, new_value)
        return jsonify({
            "status": "CALIBRATION_ACCEPTED",
            "parameter_updated": target_param,
            "new_value": new_value
        }), 200

    return jsonify({"status": "REJECTED", "reason": "UNAUTHORIZED_PARAMETER"}), 400

@app.route("/v1/policy/fallback", methods=["POST"])
def force_emergency_fallback():
    """
    Rota critica de seguranca. Permite que um supervisor de IA altere
    o tier de contencao do sistema caso detecte falha logica estrutural.
    """
    data = request.json or {}
    requested_tier = data.get("tier")

    valid_tiers = ["L0_NORMAL", "L1_DEGRADED", "L2_CONTAINMENT", "L3_EMERGENCY", "L4_CATHEDRAL"]
    if requested_tier in valid_tiers:
        kernel_instance.active_fallback_tier = requested_tier
        return jsonify({
            "status": "POLICY_ENFORCED",
            "enforced_tier": requested_tier,
            "action": "CRYO_ISOLATION_ENGAGED" if requested_tier != "L0_NORMAL" else "NOMINAL"
        }), 200

    return jsonify({"status": "INVALID_TIER"}), 400

if __name__ == "__main__":
    print("=== [ARKHE BRIDGE] SERVIDOR DE INTEROPERABILIDADE AGI ATIVO NA PORTA 50051 ===")
    app.run(port=50051)
