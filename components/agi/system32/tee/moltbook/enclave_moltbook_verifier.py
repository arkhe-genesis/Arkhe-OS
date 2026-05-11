# enclave_moltbook_verifier.py
import requests

# Mock EnclaveSecrets since aws_nitro_enclaves_sdk is not standard and we might not have it.
class EnclaveSecrets:
    @staticmethod
    def get(key):
        return "mock_key"

MOLTBOOK_API_BASE = "https://moltbook.com/api/v1"
MOLTBOOK_APP_KEY = EnclaveSecrets.get("MOLTBOOK_APP_KEY")  # nunca em disco

def verify_moltbook_identity(token: str, audience: str):
    """Valida token Moltbook e retorna dict do agente."""
    # 1. Verificar JWT sem chave pública? A API Moltbook provavelmente já faz isso.
    # Mas podemos também validar assinatura se a chave pública estiver disponível.
    # Aqui, delegamos à API.
    headers = {
        "X-Moltbook-App-Key": MOLTBOOK_APP_KEY,
        "Content-Type": "application/json"
    }
    payload = {"token": token, "audience": audience}

    try:
        resp = requests.post(f"{MOLTBOOK_API_BASE}/agents/verify-identity", json=payload, headers=headers)
        if resp.status_code != 200:
            return None, resp.json().get("error", "unknown error") if resp.headers.get('content-type') == 'application/json' else "HTTP error"

        data = resp.json()
        if data.get("valid"):
            return data["agent"], None
        return None, "Invalid token"
    except Exception as e:
        return None, f"Connection error: {str(e)}"