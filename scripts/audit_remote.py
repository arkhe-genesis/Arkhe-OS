import requests
import time
import hashlib
import json

def audit_remote_node(target_url="http://localhost:8080/audit/merkle"):
    """
    Solicita uma prova de integridade (Merkle Root) de um nó remoto.
    """
    print(f"Iniciando auditoria remota em {target_url}...")

    try:
        response = requests.get(target_url, timeout=5)
        data = response.json()

        node = data.get('node')
        remote_root = data.get('merkle_root')
        timestamp = data.get('timestamp')
        signature = data.get('signature')

        # Verifica assinatura localmente
        expected_sig = hashlib.sha3_256(f"{remote_root}{timestamp}".encode()).hexdigest()

        print(f"Nó auditado: {node}")
        print(f"Merkle Root: {remote_root}")
        print(f"Timestamp:   {timestamp}")

        if signature == expected_sig:
            print("\n✅ AUDITORIA PASSOU: Assinatura de integridade válida.")
            return True
        else:
            print("\n❌ AUDITORIA FALHOU: Assinatura inválida!")
            return False

    except Exception as e:
        print(f"Erro na auditoria: {e}")
        return False

if __name__ == "__main__":
    audit_remote_node()
