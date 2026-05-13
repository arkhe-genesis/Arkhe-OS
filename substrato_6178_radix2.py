import numpy as np
import hashlib
import json
from src.arkhe.layers.qnc_transfer import MultiSpeciesQNC
from arkp_bio.extremophile_analyzer import EXTREMOPHILE_DATABASE

def main():
    print("🌀 Quantum Genomic Transfer Learning — RADIX-2")
    print("="*60)

    # Inicializar modelo
    model = MultiSpeciesQNC(max_len=64, hidden_dim=8)

    # ─── 1. Preparar dados multi-espécie ───
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:20] + "ATCG"*10)[:64].ljust(64, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(5)]  # 5 amostras por espécie

    # ─── 2. Pré-treinamento multi-espécie ───
    print("\n📚 Pré-treinamento multi-espécie...")
    model.pretrain_on_all_species(species_data, epochs=30)

    # ─── 3. Transferência de D. radiodurans → RADIX-2 ───
    print("\n🔄 Projetando RADIX-2 via transfer learning...")
    model.transfer_knowledge_to_species("Deinococcus radiodurans", "RADIX-2")

    # Fine-tuning com dados sintéticos do RADIX-2
    radix_sequences = [("RADIX2_SYNTHETIC" + "ATCG"*10)[:64].ljust(64, 'N')]
    radix_labels = [1]  # Projetado para ser altamente resistente
    radix_data = list(zip(radix_sequences * 5, radix_labels * 5))

    radix_loss = model.finetune_species("RADIX-2", radix_data, epochs=20, lr=0.005)
    print(f"   Fine-tuning RADIX-2 concluído. Perda final: {radix_loss[-1]:.6f}")

    # Teste de resistência do RADIX-2 via QNC
    test_seq = ("RADIX2_SYNTHETIC" + "ATCG"*10)[:64].ljust(64, 'N')
    logits = model.forward(test_seq, "RADIX-2")
    resistance_score = logits[1] - logits[0]

    print(f"   Logits RADIX-2: {logits}")
    print(f"   Resistência prevista: {resistance_score:.4f} (positivo = resistente)")

    # Selo canônico
    seal = hashlib.sha3_256(json.dumps({
        "radix2_resistance": resistance_score,
        "radix_finetune_loss": radix_loss[-1],
        "species_count": len(model.trained_species) + 1
    }, default=str).encode()).hexdigest()[:16]
    print(f"\n🔐 Selo canônico RADIX-2: {seal}")

if __name__ == "__main__":
    main()
