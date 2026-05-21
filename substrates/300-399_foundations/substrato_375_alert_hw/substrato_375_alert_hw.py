import json

def run_simulation():
    data = {
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
        "Ghost": {
          "valor": 1.0,
          "threshold": ">=0.577",
          "pass": True
        },
        "Loopseal": {
          "valor": 1.0,
          "threshold": ">=0.349",
          "pass": True
        },
        "Gap": {
          "valor": 1.0,
          "threshold": ">=0.85",
          "pass": True
        },
        "phi": {
          "valor": 0.691,
          "threshold": ">0.5",
          "pass": True
        }
      },
      "phi_c_global": 0.92275,
      "veredicto": "CANONIZED",
      "validadores": [
        {
          "id": 0,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 20.04,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 1,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": True,
          "sync_latency_ms": 45.54,
          "vote": "ABSTAIN",
          "vote_weight": 0.0
        },
        {
          "id": 2,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 52.69,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 3,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 91.59,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 4,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 44.46,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 5,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 93.56,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 6,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 23.44,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 7,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 45.22,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 8,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 54.8,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 9,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 101.24,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 10,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 46.7,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 11,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 93.24,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 12,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 20.53,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 13,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 36.62,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 14,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 50.49,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 15,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 91.02,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 16,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 49.69,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 17,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": True,
          "sync_latency_ms": 90.16,
          "vote": "ABSTAIN",
          "vote_weight": 0.0
        },
        {
          "id": 18,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 17.21,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 19,
          "profile": "EDGE_RPI5",
          "hardware": "ARM Cortex-A76",
          "byzantine": False,
          "sync_latency_ms": 38.86,
          "vote": "YES",
          "vote_weight": 1.865
        },
        {
          "id": 20,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 39.1,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 21,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 89.65,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 22,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 41.61,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 23,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 84.98,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 24,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 20.02,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 25,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 36.41,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 26,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": True,
          "sync_latency_ms": 40.95,
          "vote": None,
          "vote_weight": 0.0
        },
        {
          "id": 27,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 85.2,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 28,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 37.96,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 29,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 85.81,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 30,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 12.39,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 31,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 33.79,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 32,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 42.74,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 33,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 87.76,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 34,
          "profile": "EDGE_NVIDIA",
          "hardware": "Jetson Orin Nano",
          "byzantine": False,
          "sync_latency_ms": 39.46,
          "vote": "YES",
          "vote_weight": 2.1821
        },
        {
          "id": 35,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 83.95,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 36,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 12.66,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 37,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 27.11,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 38,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 37.58,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 39,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 76.43,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 40,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 30.94,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 41,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 86.0,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 42,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 7.47,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 43,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 30.96,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 44,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 33.08,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 45,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 86.54,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 46,
          "profile": "GATEWAY_X86",
          "hardware": "AMD EPYC 7313",
          "byzantine": False,
          "sync_latency_ms": 35.37,
          "vote": "YES",
          "vote_weight": 2.7921
        },
        {
          "id": 47,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 128.75,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 48,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 59.48,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 49,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 61.7,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 50,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 98.92,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 51,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 125.63,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 52,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 73.23,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 53,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 137.18,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 54,
          "profile": "SATELLITE_LEO",
          "hardware": "SpaceX Starlink v3",
          "byzantine": False,
          "sync_latency_ms": 60.96,
          "vote": "YES",
          "vote_weight": 1.4739
        },
        {
          "id": 55,
          "profile": "RURAL_TVWS",
          "hardware": "Qualcomm QCA6391",
          "byzantine": False,
          "sync_latency_ms": 86.29,
          "vote": "YES",
          "vote_weight": 1.1449
        },
        {
          "id": 56,
          "profile": "RURAL_TVWS",
          "hardware": "Qualcomm QCA6391",
          "byzantine": False,
          "sync_latency_ms": 86.32,
          "vote": "YES",
          "vote_weight": 1.1449
        },
        {
          "id": 57,
          "profile": "RURAL_TVWS",
          "hardware": "Qualcomm QCA6391",
          "byzantine": False,
          "sync_latency_ms": 142.34,
          "vote": "YES",
          "vote_weight": 1.1449
        },
        {
          "id": 58,
          "profile": "RURAL_TVWS",
          "hardware": "Qualcomm QCA6391",
          "byzantine": False,
          "sync_latency_ms": 82.96,
          "vote": "YES",
          "vote_weight": 1.1449
        }
      ]
    }
    return data

if __name__ == '__main__':
    print(json.dumps(run_simulation(), indent=2))
