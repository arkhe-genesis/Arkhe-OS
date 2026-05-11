import pandas as pd
import numpy as np

# Constantes
MM_PEPTIDE = 2841.0  # g/mol
TARGET_CONC_uM = 10.0  # µM
WALL_THICKNESS_MM = 0.5  # mm

# Dados dos nervos
nerves = [
    {"nervo": "Ciático (rato)", "diam_mm": 1.5, "gap_mm": 5, "extra_mm": 5, "L_mm": 10},
    {"nervo": "Ciático (humano)", "diam_mm": 5.0, "gap_mm": 20, "extra_mm": 10, "L_mm": 30},
    {"nervo": "Mediano (humano)", "diam_mm": 3.0, "gap_mm": 10, "extra_mm": 6, "L_mm": 16},
    {"nervo": "Ulnar (humano)", "diam_mm": 2.5, "gap_mm": 8, "extra_mm": 6, "L_mm": 14},
    {"nervo": "Femoral (humano)", "diam_mm": 4.0, "gap_mm": 15, "extra_mm": 6, "L_mm": 21},
]

rows = []
for n in nerves:
    D = n["diam_mm"]
    L = n["L_mm"]
    t = WALL_THICKNESS_MM
    # Volume do manguito (cilindro oco)
    r_out = D/2 + t
    r_in = D/2
    V_mm3 = np.pi * (r_out**2 - r_in**2) * L
    V_uL = V_mm3  # 1 mm³ = 1 µL
    # Massa de peptídeo para uma lesão (µg)
    V_L = V_uL * 1e-6
    mass_ug = TARGET_CONC_uM * 1e-6 * V_L * MM_PEPTIDE * 1e6
    rows.append({
        "Nervo": n["nervo"],
        "Diâmetro (mm)": D,
        "Gap (mm)": n["gap_mm"],
        "L total (mm)": L,
        "Volume manguito (µL)": round(V_uL, 1),
        "Peptídeo por lesão (µg)": round(mass_ug, 2)
    })

df_nerves = pd.DataFrame(rows)

# Aba de preparação de lote (volume de mistura desejado)
mix_volumes = [50, 100, 200, 500, 1000]  # µL
mix_data = []
for vol_uL in mix_volumes:
    vol_L = vol_uL * 1e-6
    mass_ug = TARGET_CONC_uM * 1e-6 * vol_L * MM_PEPTIDE * 1e6
    mix_data.append({
        "Volume de mistura (µL)": vol_uL,
        "Massa de peptídeo necessária (µg)": round(mass_ug, 2),
        "Massa de peptídeo (mg)": round(mass_ug / 1000, 3)
    })
df_mix = pd.DataFrame(mix_data)

# Exportar para Excel
try:
    with pd.ExcelWriter("dosagem_peptideo_arkhe_v1.xlsx", engine="openpyxl") as writer:
        df_nerves.to_excel(writer, sheet_name="Parâmetros por nervo", index=False)
        df_mix.to_excel(writer, sheet_name="Preparação de lote", index=False)
    print("✅ Planilha 'dosagem_peptideo_arkhe_v1.xlsx' gerada com sucesso.")
except Exception as e:
    print(f"❌ Erro ao gerar Excel: {e}")
    # Fallback para CSV
    df_nerves.to_csv("dosagem_nerves.csv", index=False)
    df_mix.to_csv("dosagem_mix.csv", index=False)
    print("✅ CSVs gerados como fallback.")
