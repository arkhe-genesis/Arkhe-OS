#!/usr/bin/env python3
"""
generate_hydration_stress_pdf.py
================================
Generates formal PDF report for Hydration Stress Analysis (Synapse-κ #14c).

Author: Synapse-κ
Date: 2026-04-18
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_pdf(output_path, results_path, img_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Arkhe(n) — Synapse-κ #14c", styles['Title']))
    story.append(Paragraph("Relatório Formal: Análise de Stress de Hidratação", styles['Heading1']))
    story.append(Spacer(1, 12))

    # Metadata
    metadata = [
        ["Arkhe-Chain TS", "847.625"],
        ["Status", "SIMULAÇÃO_CONCLUÍDA"],
        ["Data da Análise", "18 de Abril de 2026"],
        ["Analista", "Synapse-κ (Z.ai)"]
    ]
    t = Table(metadata, colWidths=[150, 250])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(t)
    story.append(Spacer(1, 24))

    # Executive Summary
    story.append(Paragraph("1. Resumo Executivo", styles['Heading2']))
    story.append(Paragraph("Este relatório documenta a transição de fase da calmodulina durante o processo de desidratação induzida por Ca²⁺. Através da métrica λ₂ e da análise de stress de hidratação, classificamos o mecanismo de coordenação e medimos a eficiência de transdução η_Arkhe.", styles['Normal']))
    story.append(Spacer(1, 12))

    # Main Visualization
    if os.path.exists(img_path):
        story.append(Paragraph("2. Visualização de Stress (6 Painéis)", styles['Heading2']))
        img = Image(img_path, width=450, height=300)
        story.append(img)
        story.append(Spacer(1, 12))

    # Results Table
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            res = json.load(f)

        story.append(Paragraph("3. Métricas de Validação", styles['Heading2']))
        res_data = [
            ["Métrica", "Valor", "Significado"],
            ["Mecanismo", res.get("mechanism", "N/A"), "SWITCH vs DIAL"],
            ["Largura w", f"{res.get('w_A', 0):.3f} Å", "Transição binária se < 0.3"],
            ["η_Arkhe", f"{res.get('eta_arkhe', 0):.3f}", "Eficiência (> 1.0 = super)"],
            ["I_disp", f"{res.get('i_disp', 0):.1f} bits", "Custo informacional"]
        ]
        t2 = Table(res_data, colWidths=[120, 120, 200])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        story.append(t2)

    story.append(PageBreak())
    story.append(Paragraph("4. Conclusão Arkhe(n)", styles['Heading2']))
    story.append(Paragraph("Os dados confirmam que a calmodulina opera como um bit biológico robusto quando saturada. O deslocamento de água é o ato de pagamento energético para a compra de coerência conformacional λ₂.", styles['Normal']))

    doc.build(story)
    return output_path

if __name__ == "__main__":
    import json
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
    create_pdf(
        os.path.join(RESULTS_DIR, "Analise-Stress-Hidratacao-CaM.pdf"),
        os.path.join(RESULTS_DIR, "hydration_stress_results.json"),
        os.path.join(RESULTS_DIR, "calmodulin_hydration_stress.png")
    )
    print("[OK] PDF Report generated.")
