import time
import requests

def run_echo_ping(target_url="http://localhost:8080/quantum"):
    """
    Protocolo ECO: Mede o tempo de reação do manifold remoto.
    """
    print(f"Enviando Ping Quântico para {target_url}...")

    payload = {"action": "entangle", "target": "Local", "target2": "Remote"}

    start = time.time()
    try:
        # 1. Entangle
        r1 = requests.post(target_url, json=payload, timeout=5)
        # 2. Observe
        payload_obs = {"action": "observe", "target": "Remote"}
        r2 = requests.post(target_url, json=payload_obs, timeout=5)

        end = time.time()

        latency_ms = (end - start) * 1000
        print(f"Eco recebido: {latency_ms:.2f}ms (tempo de reação do manifold)")
        return latency_ms
    except Exception as e:
        print(f"Falha no Eco: {e}")
        return None

if __name__ == "__main__":
    # Nota: requer gateway rodando
    print("Nota: Este ping requer que o gateway_bridge.py esteja rodando na porta 8080.")
    run_echo_ping()
