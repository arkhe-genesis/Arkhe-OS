# qnc_transfer_demo.py
import numpy as np
from src.arkhe.layers.qnc_transfer import MultiSpeciesQNC
from arkp_bio.extremophile_analyzer import EXTREMOPHILE_DATABASE

print("🌀 Quantum Genomic Transfer Learning — Demonstração")
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
print("\n📚 Pré-treinamento multi-espécie (5 organismos):")
pretrain_loss = model.pretrain_on_all_species(species_data, epochs=30)

# ─── 3. Transferência de D. radiodurans → T. gammatolerans ───
print("\n🔄 Teste de transferência:")
print("   Deinococcus radiodurans (15 kGy) → Thermococcus gammatolerans (30 kGy)")

# Dados da espécie alvo
target_seq = ("Thermococcus gamma" + "ATCG"*10)[:64].ljust(64, 'N')
target_data = [(target_seq, 1) for _ in range(10)]

# Medir eficiência
eff = model.compute_transfer_efficiency(
    "Deinococcus radiodurans",
    "Thermococcus gammatolerans",
    target_data
)
print(f"   Eficiência de transferência: {eff*100:.1f}%")

# ─── 4. Zero-shot prediction para uma espécie nova ───
print("\n🎯 Predição zero-shot para espécie desconhecida:")
new_seq = "Pyrococcus furiosus"[:20].ljust(64, 'N') + "ATCG"*10
pred, conf = model.zero_shot_predict(new_seq[:64])
print(f"   Pyrococcus furiosus: pred={pred} (1=resistente), confiança={conf:.4f}")
