#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_synthesis_monitor.py
Monitor de progresso SPPS para o peptídeo Arkhe-v1.
Rastreia o acoplamento de resíduos e o cronograma de 28 dias.
"""

import datetime
import json
import os

class ArkheSynthesisMonitor:
    def __init__(self):
        # Início: 2026-04-07
        self.start_date = datetime.date(2026, 4, 7)
        self.target_date = self.start_date + datetime.timedelta(days=28)
        self.sequence = "GRGFSGGGGRGGFGGGGRGGYGGGGRGGG"
        self.total_residues = len(self.sequence)

    def get_progress(self):
        """Retorna progresso da síntese baseado no tempo decorrido"""
        # Para a simulação, assumimos que 'hoje' é D+3 (10/04/2026)
        simulated_today = self.start_date + datetime.timedelta(days=3)

        days_elapsed = (simulated_today - self.start_date).days
        days_remaining = 28 - days_elapsed
        progress_pct = (days_elapsed / 28) * 100

        # Resíduos acoplados (acelera no início para simulação)
        current_residue = min(self.total_residues, int((days_elapsed / 20) * self.total_residues) + 2)

        status = {
            "batch_id": "BATCH-847.760-ARKHE-v1",
            "timestamp": simulated_today.isoformat(),
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "progress_pct": round(progress_pct, 1),
            "current_residue": current_residue,
            "total_residues": self.total_residues,
            "synthesized_fragment": self.sequence[:current_residue],
            "current_phase": "SPPS_COUPLING_BLOCK_RGG",
            "estimated_completion": self.target_date.isoformat()
        }
        return status

    def render_dashboard(self):
        status = self.get_progress()
        print("\n" + "═"*60)
        print(f"║  🧬 STATUS DE SÍNTESE: ARKHE-v1 (Synapse 847.760)")
        print("═"*60)
        print(f"║  Dias:           {status['days_elapsed']}/28 (Restam {status['days_remaining']})")
        print(f"║  Progresso:       [{'#'*int(status['progress_pct']/5)}{'-'*(20-int(status['progress_pct']/5))}] {status['progress_pct']}%")
        print(f"║  Resíduo atual:   {status['current_residue']}/{status['total_residues']}")
        print(f"║  Sequência:       {status['synthesized_fragment']}...")
        print(f"║  Fase:           {status['current_phase']}")
        print("═"*60)

        # Salvar Log
        with open("arkhe_synthesis_progress.json", "w") as f:
            json.dump(status, f, indent=2)

if __name__ == "__main__":
    monitor = ArkheSynthesisMonitor()
    monitor.render_dashboard()
