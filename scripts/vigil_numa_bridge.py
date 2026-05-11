#!/usr/bin/env python3
"""
BRIDGE VIGIL-NUMA (vigil_numa_bridge.py)
Conecta a API do numa ao Monitor Entrópico da Catedral.
"""

import time
import requests
import argparse
import sys

def poll_numa_blocking(api_url):
    """Consulta as estatísticas de bloqueio do numa."""
    try:
        # Nota: O numa v0.14.2 expõe estatísticas em /api/stats ou similar.
        # Ajustamos para o endpoint genérico de estatísticas.
        response = requests.get(f"{api_url}/api/stats", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[Vigil-Numa] Erro ao conectar: {e}", file=sys.stderr)
    return None

def main():
    parser = argparse.ArgumentParser(description="Ponte Vigil-Numa para a Catedral.")
    parser.add_argument("--numa-api", default="http://localhost:5380", help="URL da API do numa")
    parser.add_argument("--gateway", default="http://localhost:8080/entropy", help="URL do Gateway para reporte")
    parser.add_argument("--interval", type=float, default=5.0, help="Intervalo de consulta")
    args = parser.parse_args()

    print(f"Iniciando ponte Vigil-Numa... (Alvo: {args.numa_api})")

    last_blocked_count = 0

    while True:
        stats = poll_numa_blocking(args.numa_api)
        if stats:
            # Exemplo de extração de dados (baseado na spec do numa)
            total_queries = stats.get('total_queries', 0)
            blocked_queries = stats.get('blocked_queries', 0)

            if blocked_queries > last_blocked_count:
                new_blocks = blocked_queries - last_blocked_count
                print(f"[Vigil-Numa] {new_blocks} novas ameaças de entropia bloqueadas.")

                # Reporta ao monitor de entropia via gateway
                try:
                    payload = {
                        "source": "numa_dns",
                        "blocked_count": new_blocks,
                        "total_queries": total_queries
                    }
                    requests.post(args.gateway, json=payload, timeout=1)
                except:
                    pass

                last_blocked_count = blocked_queries

        time.sleep(args.interval)

if __name__ == "__main__":
    main()
