#!/usr/bin/env python3
"""
arkhe_inoculation_heatmap.py
Arkhe(n) – Gera mapa de calor de inoculação para placa de 96 poços,
com base nos tempos de resfriamento dos diferentes volumes de mistura.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import os

# ============================================================================
# DADOS DE VOLUMES E TEMPOS DE RESFRIAMENTO (DA SIMULAÇÃO TÉRMICA)
# ============================================================================
COOLING_DATA = {
    "Ciatico_Rato": {"volume_ul": 31.42, "cooling_time_s": 22},
    "Ciatico_Humano": {"volume_ul": 259.18, "cooling_time_s": 84},
    "Mediano_Humano": {"volume_ul": 87.96, "cooling_time_s": 43},
    "Ulnar_Humano": {"volume_ul": 65.97, "cooling_time_s": 36},
    "Femoral_Humano": {"volume_ul": 148.44, "cooling_time_s": 58},
    "Tibial_Humano": {"volume_ul": 204.20, "cooling_time_s": 71},
    "Radial_Humano": {"volume_ul": 113.10, "cooling_time_s": 49},
    "Peroneiro_Humano": {"volume_ul": 87.96, "cooling_time_s": 43},
    "Controle": {"volume_ul": 50.0, "cooling_time_s": 30},
}

# Plate geometry for coordinate mapping
WELL_PITCH_MM = 9.0
ORIGIN_A1_MM = (14.0, 11.0)

# ============================================================================
# FUNÇÕES
# ============================================================================
def well_id_to_xy(well_id: str):
    row_letter = well_id[0].upper()
    col_num = int(well_id[1:])
    row_index = ord(row_letter) - ord('A')
    col_index = col_num - 1
    x = col_index * WELL_PITCH_MM
    y = row_index * WELL_PITCH_MM
    return x, y

def load_layout(csv_file):
    df = pd.read_csv(csv_file)
    plate = np.empty((8, 12), dtype=object)
    for _, row in df.iterrows():
        well = row['well']
        nerve = row['nerve_type']
        row_idx = ord(well[0].upper()) - ord('A')
        col_idx = int(well[1:]) - 1
        plate[row_idx, col_idx] = nerve
    return plate

def get_cooling_time(nerve_type):
    if nerve_type in COOLING_DATA:
        return COOLING_DATA[nerve_type]["cooling_time_s"]
    return 30

def generate_inoculation_order(plate):
    cooling_times = np.zeros((8, 12))
    for i in range(8):
        for j in range(12):
            nerve = plate[i, j]
            if nerve is not None:
                cooling_times[i, j] = get_cooling_time(nerve)
            else:
                cooling_times[i, j] = 999

    flat_times = cooling_times.flatten()
    unique_times = sorted(set(flat_times))
    time_to_order = {t: idx+1 for idx, t in enumerate(unique_times)}

    order_matrix = np.zeros((8, 12), dtype=int)
    for i in range(8):
        for j in range(12):
            order_matrix[i, j] = time_to_order[cooling_times[i, j]]

    if 999 in time_to_order:
        max_order = max([v for k, v in time_to_order.items() if k != 999])
        order_matrix[cooling_times == 999] = max_order + 1

    return order_matrix, cooling_times

def plot_inoculation_heatmap(plate, order_matrix, cooling_times, output_file="inoculation_heatmap.png"):
    fig, ax = plt.subplots(figsize=(14, 10))
    im = ax.imshow(order_matrix, cmap='viridis', interpolation='nearest', aspect='equal')
    plt.colorbar(im, ax=ax, label='Ordem de Inoculação (1 = primeiro)')

    ax.set_xticks(np.arange(12))
    ax.set_yticks(np.arange(8))
    ax.set_xticklabels([str(i+1) for i in range(12)])
    ax.set_yticklabels([chr(ord('A')+i) for i in range(8)])
    ax.set_xlabel('Coluna')
    ax.set_ylabel('Linha')
    ax.set_title('Mapa de Calor de Inoculação Arkhe(n) – Ordem Recomendada')

    for i in range(8):
        for j in range(12):
            nerve = plate[i, j]
            if nerve is not None:
                t_cool = cooling_times[i, j]
                text = f"{nerve.split('_')[0]}\n{t_cool:.0f}s"
                ax.text(j, i, text, ha='center', va='center', fontsize=8, color='white',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6))
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"[Arkhe] Mapa de calor salvo como {output_file}")

def export_order_table(order_matrix, cooling_times, plate, output_csv="inoculation_order_autozero.csv"):
    rows = []
    for i in range(8):
        for j in range(12):
            well = f"{chr(ord('A')+i)}{j+1}"
            nerve = plate[i, j]
            if nerve is not None:
                order = int(order_matrix[i, j])
                t_cool = float(cooling_times[i, j])
                vol = COOLING_DATA.get(nerve, {}).get("volume_ul", 50.0)
                x, y = well_id_to_xy(well)
                rows.append({
                    "Well": well,
                    "Nerve_Type": nerve,
                    "Volume_uL": vol,
                    "Inoculation_Order": order,
                    "T_zero_C": 25.0, # Baseline from Auto-Zero
                    "X_mm": x,
                    "Y_mm": y
                })
    df = pd.DataFrame(rows)
    df = df.sort_values("Inoculation_Order")
    df.to_csv(output_csv, index=False)
    print(f"[Arkhe] Ordem de inoculação exportada para {output_csv}")

def main():
    print("=" * 60)
    print("ARKHE(n) – Mapa de Calor de Inoculação")
    print("=" * 60)

    layout_file = "plate_layout.csv"
    if not os.path.exists(layout_file):
        print(f"Criando layout de exemplo ({layout_file})")
        nerves = [
            "Ciatico_Rato", "Mediano_Humano", "Ulnar_Humano",
            "Femoral_Humano", "Tibial_Humano", "Radial_Humano",
            "Peroneiro_Humano", "Ciatico_Humano"
        ]
        rows = []
        well_idx = 1
        for row_letter in ['A','B','C','D','E','F','G','H']:
            for col in range(1, 13):
                if well_idx <= len(nerves)*3:
                    nerve = nerves[(well_idx-1)//3]
                else:
                    nerve = "Controle"
                rows.append({"well": f"{row_letter}{col}", "nerve_type": nerve})
                well_idx += 1
        pd.DataFrame(rows).to_csv(layout_file, index=False)

    plate = load_layout(layout_file)
    order_matrix, cooling_times = generate_inoculation_order(plate)
    plot_inoculation_heatmap(plate, order_matrix, cooling_times)
    export_order_table(order_matrix, cooling_times, plate)

    max_order = int(np.max(order_matrix))
    print(f"\n✅ Ordem de inoculação gerada para {max_order} passos.")
    print("   Inicie a pipetagem pelas células com ordem 1 e prossiga até ordem máxima.")
    print("   Aguarde pelo menos 90 segundos após a fotopolimerização antes de iniciar a inoculação.")

if __name__ == "__main__":
    main()
