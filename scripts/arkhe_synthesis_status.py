#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_synthesis_status.py
Monitor de progresso da síntese do peptídeo Arkhe-v1 (BATCH-847.760).
Rastreia o cronograma de 28 dias e critérios de QC.
"""

import json
import time
from datetime import datetime, timezone, timedelta

class ArkheSynthesisTracker:
    def __init__(self, start_date_str="2026-04-07"):
        self.batch_id = "BATCH-847.760-ARKHE-v1"
        self.start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        self.target_date = self.start_date + timedelta(days=28)
        self.total_residues = 32
        self.sequence = "GRGFSGGGGRGGFGGGGRGGYGGGGRGGG"

    def get_current_status(self):
        # Em uma aplicação real, isso consultaria o sistema do fornecedor
        now = datetime.now()
        # Para fins de simulação, assumimos que hoje é D+3
        simulated_now = self.start_date + timedelta(days=3)

        days_elapsed = (simulated_now - self.start_date).days
        progress_pct = (days_elapsed / 28) * 100

        # Estimar resíduos acoplados (lineal para simulação)
        residues_coupled = min(self.total_residues, int((days_elapsed / 20) * self.total_residues))

        status = {
            "batch_id": self.batch_id,
            "peptide": "Arkhe-v1",
            "progress_pct": round(progress_pct, 1),
            "days_elapsed": days_elapsed,
            "days_remaining": 28 - days_elapsed,
            "current_phase": "SPPS_COUPLING",
            "residues_coupled": residues_coupled,
            "total_residues": self.total_residues,
            "sequence_progress": self.sequence[:residues_coupled],
            "target_delivery": self.target_date.strftime("%Y-%m-%d"),
            "qc_metrics": {
                "expected_mw": 2840.6,
                "purity_target": 98.0,
                "endotoxin_limit": 0.5
            }
        }
        return status

    def print_dashboard(self, status):
        print("\n" + "="*60)
        print(f"║  🧬 STATUS DE SÍNTESE: {status['peptide']} ({status['batch_id']})")
        print("="*60)
        print(f"║  Progresso:       [{'#'*int(status['progress_pct']/5)}{'-'*(20-int(status['progress_pct']/5))}] {status['progress_pct']}%")
        print(f"║  Dias:           {status['days_elapsed']}/28 (Restam {status['days_remaining']})")
        print(f"║  Resíduos:       {status['residues_coupled']}/{status['total_residues']}")
        print(f"║  Fase Atual:     {status['current_phase']}")
        print(f"║  Entrega Alvo:   {status['target_delivery']}")
        print("="*60)

def run_tracker():
    tracker = ArkheSynthesisTracker()
    status = tracker.get_current_status()
    tracker.print_dashboard(status)

    # Salvar log
    with open("arkhe_synthesis_report.json", "w") as f:
        json.dump(status, f, indent=2)
    print("\n✅ Relatório de síntese atualizado em arkhe_synthesis_report.json")

if __name__ == "__main__":
    run_tracker()
