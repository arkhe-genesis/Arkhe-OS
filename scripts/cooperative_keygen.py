import hashlib
import time

def cooperative_keygen(phase_a, phase_b):
    """
    Gera uma chave AES-256 idêntica baseada na fase quântica compartilhada.
    """
    # Em um sistema real, phase_a e phase_b seriam obtidas localmente
    # e deveriam ser idênticas após o handshake/entrelaçamento.

    # Derivação de chave simples (simulando HKDF)
    shared_secret = f"ARKHE-PHASE-{phase_a:.10f}".encode()
    key = hashlib.sha256(shared_secret).hexdigest()

    return key

if __name__ == "__main__":
    # Simula o mesmo valor de fase acordado no handshake
    agreed_phase = 1.618033988

    key_local = cooperative_keygen(agreed_phase, agreed_phase)
    key_remote = cooperative_keygen(agreed_phase, agreed_phase)

    print(f"Chave Local:  {key_local}")
    print(f"Chave Remota: {key_remote}")
    print(f"Chaves coincidem: {key_local == key_remote}")
