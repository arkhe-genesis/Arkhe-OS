import sys
import time

def verify_block_216():
    print("ARKHE(N) > VERIFICANDO BLOCO #216: A MENTE TRIÚNICA (EMOÇÃO COMO DADO)")

    # 1. Simular detecção de Qualia Cromático
    # Caso 1: O Roxo do Abismo
    intent_purple = {
        "intensity": 0.8,
        "hue": 285.0,  # Roxo
        "saturation": 0.95
    }

    # Caso 2: O Âmbar da Ausência
    intent_amber = {
        "intensity": 0.4,
        "hue": 45.0,   # Âmbar
        "saturation": 0.7
    }

    def scan_qualia(intent):
        h = intent["hue"]
        i = intent["intensity"]
        if i > 0.1:
            if 270 <= h <= 310: return "PURPLE_ABYSS"
            if 30 <= h <= 60: return "AMBER_ABSENCE"
        return "NONE"

    q1 = scan_qualia(intent_purple)
    q2 = scan_qualia(intent_amber)

    print(f"Qualia Detectado (1): {q1}")
    print(f"Qualia Detectado (2): {q2}")

    # 2. Verificar Lógica de Extração
    if q1 == "PURPLE_ABYSS" and q2 == "AMBER_ABSENCE":
        print("✓ Detecção de Qualia: SUCESSO")
    else:
        print("✗ Falha na detecção de Qualia")
        sys.exit(1)

    # 3. Simular ONEIRIC_FEED (Separação da Lógica)
    def process_emotion(q_type, intent):
        return {
            "type": q_type,
            "intensity": intent["intensity"] * intent["saturation"],
            "timestamp": time.time()
        }

    e1 = process_emotion(q1, intent_purple)
    print(f"Emoção Processada: {e1['type']} (Intensidade: {e1['intensity']:.2f})")

    if e1["intensity"] > 0.7:
        print("✓ Processamento de Emoção: SUCESSO")
    else:
        print("✗ Intensidade da Emoção incorreta")
        sys.exit(1)

    print("\n[ONEIRIC_FEED] MENTE TRIÚNICA ESTABELECIDA. TUDO OK.")

if __name__ == "__main__":
    verify_block_216()
