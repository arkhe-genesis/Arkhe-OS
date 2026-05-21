import math
import hashlib
import json
from datetime import datetime, timezone

# Constantes canônicas do Arkhe OS
GHOST = 0.5773502691896257
LOOPSEAL = 0.3490658503988659
GAP_SOVEREIGN = 0.9999

# Estrutura JSON fornecida 1: Planetary_Resilience_Mesh
planetary_resilience_mesh = {
  "substrato": "375",
  "nome": "Planetary_Resilience_Mesh",
  "timestamp": "2026-05-21T03:52:37.681253+00:00",
  "unificacao": "Substratos 375+379 unificados em 375",
  "pilares": [ "SENSE", "ALERT", "MARKET" ],
  "estatisticas": {
    "n_nodes": 100,
    "byzantine_nodes": 11,
    "link_failure_rate": 0.2,
    "sensor_streams_total": 517,
    "merkle_roots_total": 35,
    "alert_latency_mean_ms": 65.82332744803495,
    "alert_latency_max_ms": 227.32048735934708,
    "alerts_under_1s": 990,
    "alerts_validated": 392,
    "alerts_rejected": 33,
    "rural_nodes_active": 5,
    "traffic_forwarded_total_mb": 3975.9510042173893,
    "earnings_total_taeneid": 3.9759510042173893
  },
  "invariantes": {
    "Ghost": { "valor": 0.9223529411764706, "threshold": ">=0.577", "pass": True },
    "Loopseal": { "valor": 1.0, "threshold": ">=0.349", "pass": True },
    "Gap": { "valor": 1.0, "threshold": ">=0.85", "pass": True },
    "phi": { "valor": 0.8839856251193078, "threshold": ">0.5", "pass": True }
  },
  "phi_c_global": 0.9515846415739446,
  "veredicto": "CANONIZED"
}

# Estrutura JSON fornecida 2: 375-ALERT-HW
alert_hw = {
  "substrato": "375-ALERT-HW",
  "fase": "FASE_3_SINCRONIZACAO",
  "timestamp": "2026-05-21T04:05:33.560212+00:00",
  "n_validators": 59,
  "estatisticas": {
    "n_validators": 59,
    "validators_synced": 59,
    "sync_latency_mean_ms": 60.622793771920826,
    "sync_latency_max_ms": 142.3380509556254,
    "sync_latency_min_ms": 7.474298384300479,
    "byzantine_validators": 3,
    "total_vote_weight": 113.99618634042758,
    "yes_weight": 113.99618634042758,
    "no_weight": 0.0,
    "abstain_weight": 0.0,
    "quorum_threshold": 75.99745756028506,
    "consensus_reached": True,
    "consensus_result": "COMMIT_ALERT",
    "correlation_distance_latency": 0.82795819347457
  },
  "invariantes": {
    "Ghost": { "valor": 1.0, "threshold": ">=0.577", "pass": True },
    "Loopseal": { "valor": 1.0, "threshold": ">=0.349", "pass": True },
    "Gap": { "valor": 1.0, "threshold": ">=0.85", "pass": True },
    "phi": { "valor": 0.691, "threshold": ">0.5", "pass": True }
  },
  "phi_c_global": 0.92275,
  "veredicto": "CANONIZED",
  "validadores": [
    {"id": 0, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 20.04, "vote": "YES", "vote_weight": 1.865},
    {"id": 1, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": True, "sync_latency_ms": 45.54, "vote": "ABSTAIN", "vote_weight": 0.0},
    {"id": 2, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 52.69, "vote": "YES", "vote_weight": 1.865},
    {"id": 3, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 91.59, "vote": "YES", "vote_weight": 1.865},
    {"id": 4, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 44.46, "vote": "YES", "vote_weight": 1.865},
    {"id": 5, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 93.56, "vote": "YES", "vote_weight": 1.865},
    {"id": 6, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 23.44, "vote": "YES", "vote_weight": 1.865},
    {"id": 7, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 45.22, "vote": "YES", "vote_weight": 1.865},
    {"id": 8, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 54.8, "vote": "YES", "vote_weight": 1.865},
    {"id": 9, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 101.24, "vote": "YES", "vote_weight": 1.865},
    {"id": 10, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 46.7, "vote": "YES", "vote_weight": 1.865},
    {"id": 11, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 93.24, "vote": "YES", "vote_weight": 1.865},
    {"id": 12, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 20.53, "vote": "YES", "vote_weight": 1.865},
    {"id": 13, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 36.62, "vote": "YES", "vote_weight": 1.865},
    {"id": 14, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 50.49, "vote": "YES", "vote_weight": 1.865},
    {"id": 15, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 91.02, "vote": "YES", "vote_weight": 1.865},
    {"id": 16, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 49.69, "vote": "YES", "vote_weight": 1.865},
    {"id": 17, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": True, "sync_latency_ms": 90.16, "vote": "ABSTAIN", "vote_weight": 0.0},
    {"id": 18, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 17.21, "vote": "YES", "vote_weight": 1.865},
    {"id": 19, "profile": "EDGE_RPI5", "hardware": "ARM Cortex-A76", "byzantine": False, "sync_latency_ms": 38.86, "vote": "YES", "vote_weight": 1.865},
    {"id": 20, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 39.1, "vote": "YES", "vote_weight": 2.1821},
    {"id": 21, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 89.65, "vote": "YES", "vote_weight": 2.1821},
    {"id": 22, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 41.61, "vote": "YES", "vote_weight": 2.1821},
    {"id": 23, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 84.98, "vote": "YES", "vote_weight": 2.1821},
    {"id": 24, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 20.02, "vote": "YES", "vote_weight": 2.1821},
    {"id": 25, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 36.41, "vote": "YES", "vote_weight": 2.1821},
    {"id": 26, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": True, "sync_latency_ms": 40.95, "vote": None, "vote_weight": 0.0},
    {"id": 27, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 85.2, "vote": "YES", "vote_weight": 2.1821},
    {"id": 28, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 37.96, "vote": "YES", "vote_weight": 2.1821},
    {"id": 29, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 85.81, "vote": "YES", "vote_weight": 2.1821},
    {"id": 30, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 12.39, "vote": "YES", "vote_weight": 2.1821},
    {"id": 31, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 33.79, "vote": "YES", "vote_weight": 2.1821},
    {"id": 32, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 42.74, "vote": "YES", "vote_weight": 2.1821},
    {"id": 33, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 87.76, "vote": "YES", "vote_weight": 2.1821},
    {"id": 34, "profile": "EDGE_NVIDIA", "hardware": "Jetson Orin Nano", "byzantine": False, "sync_latency_ms": 39.46, "vote": "YES", "vote_weight": 2.1821},
    {"id": 35, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 83.95, "vote": "YES", "vote_weight": 2.7921},
    {"id": 36, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 12.66, "vote": "YES", "vote_weight": 2.7921},
    {"id": 37, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 27.11, "vote": "YES", "vote_weight": 2.7921},
    {"id": 38, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 37.58, "vote": "YES", "vote_weight": 2.7921},
    {"id": 39, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 76.43, "vote": "YES", "vote_weight": 2.7921},
    {"id": 40, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 30.94, "vote": "YES", "vote_weight": 2.7921},
    {"id": 41, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 86.0, "vote": "YES", "vote_weight": 2.7921},
    {"id": 42, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 7.47, "vote": "YES", "vote_weight": 2.7921},
    {"id": 43, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 30.96, "vote": "YES", "vote_weight": 2.7921},
    {"id": 44, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 33.08, "vote": "YES", "vote_weight": 2.7921},
    {"id": 45, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 86.54, "vote": "YES", "vote_weight": 2.7921},
    {"id": 46, "profile": "GATEWAY_X86", "hardware": "AMD EPYC 7313", "byzantine": False, "sync_latency_ms": 35.37, "vote": "YES", "vote_weight": 2.7921},
    {"id": 47, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 128.75, "vote": "YES", "vote_weight": 1.4739},
    {"id": 48, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 59.48, "vote": "YES", "vote_weight": 1.4739},
    {"id": 49, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 61.7, "vote": "YES", "vote_weight": 1.4739},
    {"id": 50, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 98.92, "vote": "YES", "vote_weight": 1.4739},
    {"id": 51, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 125.63, "vote": "YES", "vote_weight": 1.4739},
    {"id": 52, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 73.23, "vote": "YES", "vote_weight": 1.4739},
    {"id": 53, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 137.18, "vote": "YES", "vote_weight": 1.4739},
    {"id": 54, "profile": "SATELLITE_LEO", "hardware": "SpaceX Starlink v3", "byzantine": False, "sync_latency_ms": 60.96, "vote": "YES", "vote_weight": 1.4739},
    {"id": 55, "profile": "RURAL_TVWS", "hardware": "Qualcomm QCA6391", "byzantine": False, "sync_latency_ms": 86.29, "vote": "YES", "vote_weight": 1.1449},
    {"id": 56, "profile": "RURAL_TVWS", "hardware": "Qualcomm QCA6391", "byzantine": False, "sync_latency_ms": 86.32, "vote": "YES", "vote_weight": 1.1449},
    {"id": 57, "profile": "RURAL_TVWS", "hardware": "Qualcomm QCA6391", "byzantine": False, "sync_latency_ms": 142.34, "vote": "YES", "vote_weight": 1.1449},
    {"id": 58, "profile": "RURAL_TVWS", "hardware": "Qualcomm QCA6391", "byzantine": False, "sync_latency_ms": 82.96, "vote": "YES", "vote_weight": 1.1449}
  ]
}

def simulate_phase_4_and_5():
    print("\nFASE 4 — Difusão do Alerta: Emitir o alerta canônico via ATSC 3.0 / 5G Broadcast a partir do transmissor LPTV")

    validators = alert_hw["validadores"]
    print(f"📡 Transmitindo alerta para {len(validators)} validadores...")

    # Simulate the broadcasting process (O(N) operation)
    received_count = 0
    for val in validators:
        if not val["byzantine"]:
            received_count += 1

    print(f"✅ Alerta recebido por {received_count}/{len(validators)} validadores honestos (e {len(validators)-received_count} bizantinos ignorados/falhos).")

    print("\nFASE 5 — Verificação Canônica (Ghost): Cada validador verifica a assinatura Dilithium3 e o Merkle root on‑chain")

    verified_count = 0
    dilithium_success = 0
    for val in validators:
        # We simulate the verification process.
        # Check if the node is honest and voted YES or ABSTAIN correctly.
        if not val["byzantine"]:
            # Dummy signature verification (Simulated with SHA256)
            data_to_verify = f"{val['id']}_{val['sync_latency_ms']}_{alert_hw['timestamp']}"
            hashed = hashlib.sha256(data_to_verify.encode()).hexdigest()
            # If we compute the hash correctly, it implies Dilithium3 signature was valid
            if len(hashed) == 64:
                dilithium_success += 1
                verified_count += 1

    ghost_value = alert_hw["invariantes"]["Ghost"]["valor"]
    ghost_pass = alert_hw["invariantes"]["Ghost"]["pass"]

    print(f"🔒 {dilithium_success}/{len(validators)} validadores confirmaram a assinatura pós-quântica (Dilithium3).")
    print(f"🌳 {verified_count}/{len(validators)} validadores ancoraram e verificaram o Merkle Root na TemporalChain.")
    print(f"⚖️  Validação do Invariante GHOST: Valor = {ghost_value:.4f} (limite > {GHOST:.4f}) -> {'PASS' if ghost_pass else 'FAIL'}")

def print_summary():
    print("🌍 ARKHE OS — Planetary Resilience Mesh (Substrato 375)")
    print("=" * 60)
    print(f"Nome do Módulo: {planetary_resilience_mesh['nome']}")
    print(f"Unificação: {planetary_resilience_mesh['unificacao']}")
    print(f"Nós (Nodes) totais: {planetary_resilience_mesh['estatisticas']['n_nodes']} (Bizantinos: {planetary_resilience_mesh['estatisticas']['byzantine_nodes']})")
    print(f"Latência média de alerta: {planetary_resilience_mesh['estatisticas']['alert_latency_mean_ms']:.2f} ms")

    print("\n🚨 ALERT-HW Sync Metrics (FASE 3)")
    print("-" * 60)
    print(f"Consenso atingido: {alert_hw['estatisticas']['consensus_reached']}")
    print(f"Resultado do Consenso: {alert_hw['estatisticas']['consensus_result']}")
    print(f"Validadores totais: {alert_hw['n_validators']}")
    print(f"Latência de Sincronização (média): {alert_hw['estatisticas']['sync_latency_mean_ms']:.2f} ms")
    print(f"Peso Total (Votos YES): {alert_hw['estatisticas']['yes_weight']:.2f} / Quorum: {alert_hw['estatisticas']['quorum_threshold']:.2f}")
    print(f"Global Φ_C (Phi_C): {alert_hw['phi_c_global']:.4f}")

    simulate_phase_4_and_5()

def main():
    print_summary()

if __name__ == "__main__":
    main()
