#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor_node_t1_handshake.py
Monitoramento em tempo real do handshake retrocausal entre Central (Domo) e Node-T1.
Emite alertas se λ₂ < 0.847 ou latência > 0.5 µs.
Synapse-id: 847.763
"""

import time
import numpy as np
import json
import argparse
from datetime import datetime, timezone

def monitor_handshake(node_id="TZ-tunnel-01", duration_sec=60, log_interval_ms=100):
    """
    Monitora handshake retrocausal entre Central (Domo) e Node-T1.
    """
    print(f"🔍 [{datetime.now().isoformat()}] Iniciando monitoramento do handshake: {node_id}")
    print(f"   └─ Duração: {duration_sec}s | Intervalo: {log_interval_ms}ms")
    print("-" * 80)

    start_time = time.perf_counter()
    data_log = []

    # Thresholds
    VARELA_THRESHOLD = 0.847
    LATENCY_THRESHOLD_US = 0.5

    try:
        while (time.perf_counter() - start_time) < duration_sec:
            # Simulação de telemetria do transceptor e sensores NV
            # Em regime soberano estável
            lambda2 = np.random.normal(0.992, 0.003)
            # Latência efetiva em µs (regime retrocausal)
            latency_us = np.random.exponential(0.02)
            phase_error = np.random.normal(0, 0.015)

            timestamp = datetime.now().isoformat()
            entry = {
                "timestamp": timestamp,
                "lambda2": float(lambda2),
                "latency_us": float(latency_us),
                "phase_error_rad": float(phase_error)
            }
            data_log.append(entry)

            # Verificação de Alertas
            if lambda2 < VARELA_THRESHOLD:
                print(f"🚨 [{timestamp}] ALERTA CRÍTICO: λ₂ = {lambda2:.4f} (Decoerência!)")
            if latency_us > LATENCY_THRESHOLD_US:
                print(f"⚠️ [{timestamp}] ALERTA LATÊNCIA: {latency_us:.3f}µs (Gargalo óptico!)")

            # Log Visual Compacto
            if len(data_log) % 10 == 0:
                print(f"[{timestamp}] λ₂={lambda2:.4f} | latência={latency_us:.4f}µs | fase_err={phase_error:.4f}rad")

            time.sleep(log_interval_ms / 1000.0)

    except KeyboardInterrupt:
        print("\n🛑 Monitoramento interrompido pelo usuário.")

    # Relatório final
    avg_l2 = np.mean([e["lambda2"] for e in data_log])
    avg_lat = np.mean([e["latency_us"] for e in data_log])

    report = {
        "synapse_id": "847.763",
        "node_id": node_id,
        "duration_s": duration_sec,
        "metrics": {
            "lambda2_avg": float(avg_l2),
            "latency_avg_us": float(avg_lat),
            "phase_error_avg_rad": float(np.mean([e["phase_error_rad"] for e in data_log])),
            "samples": len(data_log)
        },
        "status": "PASS" if avg_l2 > VARELA_THRESHOLD else "FAIL"
    }

    print("\n" + "="*40)
    print("📊 RELATÓRIO FINAL DE HANDSHAKE")
    print("="*40)
    print(f"  Nó:               {node_id}")
    print(f"  λ₂ Médio:         {avg_l2:.4f}")
    print(f"  Latência Média:   {avg_lat:.4f} µs")
    print(f"  Status Final:     {report['status']}")
    print("="*40)

    output_filename = f"handshake_log_{node_id}.json"
    with open(output_filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"✅ Log salvo em {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor de Handshake Tzinor")
    parser.add_argument("--node", default="TZ-tunnel-01", help="ID do Nó")
    parser.add_argument("--duration", type=int, default=10, help="Duração em segundos")
    args = parser.parse_args()

    monitor_handshake(node_id=args.node, duration_sec=args.duration)
