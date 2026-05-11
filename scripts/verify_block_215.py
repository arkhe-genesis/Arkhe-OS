import sys

def verify_block_215():
    print("ARKHE(N) > VERIFICANDO BLOCO #215: O OLHO HIPERESPECTRAL")

    # 1. Simular registro de materiais
    materials = {
        0x01: {"name": "Silicon", "peaks": [1100.0]},
        0x02: {"name": "Carbon", "peaks": [270.0, 1550.0]},
        0x03: {"name": "Oxygen", "peaks": [762.0]},
        0x04: {"name": "Water", "peaks": [970.0, 1200.0, 1450.0]}
    }

    # 2. Simular leitura do sensor (espectro de água simplificado)
    # Suponha que detectamos picos em 972, 1205, 1448
    detected_peaks = [972.0, 1205.0, 1448.0]

    print(f"Picos detectados pelo sensor: {detected_peaks}")

    # 3. Lógica de correspondência (Matching)
    best_id = None
    best_score = 0.0

    for mid, data in materials.items():
        score = 0.0
        for p in data["peaks"]:
            # Verifica se há um pico detectado próximo (+/- 10nm)
            for dp in detected_peaks:
                if abs(p - dp) < 10.0:
                    score += 1.0
                    break

        final_score = score / len(data["peaks"])
        print(f"Comparando com {data['name']}: Score = {final_score:.2f}")

        if final_score > best_score:
            best_score = final_score
            best_id = mid

    # 4. Verificação final
    threshold = 0.8
    if best_id == 0x04 and best_score >= threshold:
        print(f"✓ MATERIAL IDENTIFICADO: {materials[best_id]['name']} (Score: {best_score:.2f})")
        print("✓ PROTOCOLO AKA_QUERY_MATERIAL: SUCESSO")
    else:
        print("✗ FALHA NA IDENTIFICAÇÃO DE MATERIAL")
        sys.exit(1)

if __name__ == "__main__":
    verify_block_215()
