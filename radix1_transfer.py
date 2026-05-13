# radix1_transfer.py
import numpy as np
from src.arkhe.layers.qnc_transfer import MultiSpeciesQNC
from arkp_bio.extremophile_analyzer import EXTREMOPHILE_DATABASE

# Inicializar modelo
model = MultiSpeciesQNC(max_len=64, hidden_dim=8)

# Treinar um pouco para inicializar
species_data = {}
for org in EXTREMOPHILE_DATABASE:
    seq = (org.organism_name[:20] + "ATCG"*10)[:64].ljust(64, 'N')
    label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
    species_data[org.organism_name] = [(seq, label) for _ in range(5)]

model.pretrain_on_all_species(species_data, epochs=5)

target_seq = ("Thermococcus gamma" + "ATCG"*10)[:64].ljust(64, 'N')
target_data = [(target_seq, 1) for _ in range(10)]
eff = model.compute_transfer_efficiency(
    "Deinococcus radiodurans",
    "Thermococcus gammatolerans",
    target_data
)

print("\n🧬 Transferindo conhecimento multi-espécie para RADIX-1...")

# O RADIX-1 é uma espécie sintética — não existia no treinamento.
# Usamos transferência de D. radiodurans (a mais resistente conhecida).
model.transfer_knowledge_to_species("Deinococcus radiodurans", "RADIX-1")

# Fine-tuning com dados sintéticos do RADIX-1
radix_sequences = [("RADIX1_SYNTHETIC" + "ATCG"*10)[:64].ljust(64, 'N')]
radix_labels = [1]  # Projetado para ser resistente
radix_data = list(zip(radix_sequences * 5, radix_labels * 5))

radix_loss = model.finetune_species("RADIX-1", radix_data, epochs=15, lr=0.005)
print(f"   Fine-tuning RADIX-1 concluído. Perda final: {radix_loss[-1]:.6f}")

# Teste de resistência do RADIX-1 via QNC
test_seq = ("RADIX1_SYNTHETIC" + "ATCG"*10)[:64].ljust(64, 'N')
logits = model.forward(test_seq, "RADIX-1")
print(f"   Logits RADIX-1: {logits}")
print(f"   Resistência prevista: {logits[1] - logits[0]:.4f} (positivo = resistente)")

# Selo canônico
import hashlib, json
seal = hashlib.sha3_256(json.dumps({
    "transfer_efficiency": eff,
    "radix_finetune_loss": radix_loss[-1],
    "species_count": len(model.trained_species) + 1
}, default=str).encode()).hexdigest()[:16]
print(f"\n🔐 Selo canônico: {seal}")
