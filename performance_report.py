import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class ReportMeta:
    orchestrator_version: str
    simulation_timestamp: str
    num_nodes: int
    num_electrons: int
    kolmogorov_limit: float
    total_steps: int
    firmware_hash: Optional[str] = None

    def sign(self, private_key: str) -> str:
        data = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(f"{data}{private_key}".encode()).hexdigest()[:16]

class PerformanceReport:
    def __init__(self, sim_data: Dict, metadata: ReportMeta):
        self.data = sim_data
        self.meta = metadata
        self.report_id = hashlib.sha256(
            f"{metadata.simulation_timestamp}{metadata.orchestrator_version}".encode()
        ).hexdigest()[:12]

    def convergence_metrics(self) -> Dict:
        energies = np.array(self.data['step_energies'])
        limit = self.meta.kolmogorov_limit
        threshold_idx = np.argmax(energies >= limit)
        threshold_step = threshold_idx if energies[threshold_idx] >= limit else None

        tail_start = int(0.7 * len(energies))
        if len(energies) - tail_start > 20:
            t = np.arange(tail_start, len(energies))
            e_tail = np.clip(limit - energies[tail_start:], 1e-6, None)
            log_diff = np.log(e_tail)
            slope, _ = np.polyfit(t, log_diff, 1)
            conv_rate = -slope
        else:
            conv_rate = None

        final_energy = float(energies[-1])
        energy_std = float(np.std(energies[-50:]))
        ci_lower = final_energy - 1.96 * energy_std / np.sqrt(50)
        ci_upper = final_energy + 1.96 * energy_std / np.sqrt(50)

        return {
            'threshold_step': int(threshold_step) if threshold_step is not None else None,
            'convergence_rate': float(conv_rate) if conv_rate else None,
            'final_energy': final_energy,
            'final_energy_ci': (ci_lower, ci_upper),
            'kolmogorov_reached': bool(np.any(energies >= limit)),
            'energy_variance': float(np.var(energies[-50:]))
        }

    def coherence_analysis(self) -> Dict:
        gaps = np.array(self.data['step_gaps'])
        return {
            'final_avg_gap': float(gaps[-1]),
            'min_gap': float(np.min(gaps)),
            'max_gap': float(np.max(gaps)),
            'gap_std_final': float(np.std(gaps[-100:])),
            'gap_trend_slope': float(np.polyfit(np.arange(len(gaps[-100:])), gaps[-100:], 1)[0])
        }

    def network_efficiency(self) -> Dict:
        intervals = np.array(self.data['tx_interval_history'])
        sf_vals = np.array(self.data['sf_history'])

        bw = 250e3
        payload_bits = 24 * 8
        cr = 1.25
        t_air = payload_bits * cr * (2.0 ** sf_vals) / bw
        p_tx_base = 0.1
        avg_power = p_tx_base * t_air / np.maximum(intervals, 1.0)

        total_power = np.mean(avg_power) * self.meta.num_nodes
        total_time = self.meta.total_steps * np.mean(intervals)
        total_energy_J = total_power * total_time

        total_acceleration_GeV = (self.data['step_energies'][-1] - self.data['step_energies'][0]) * self.meta.num_electrons

        return {
            'avg_power_W': float(total_power),
            'total_energy_J': float(total_energy_J),
            'acceleration_per_joule': float(total_acceleration_GeV / (total_energy_J + 1e-9)),
            'avg_airtime_ms': float(np.mean(t_air) * 1000)
        }

    def torsion_metrics(self) -> Dict:
        if 'gap_matrix' in self.data:
            gap_matrix = np.array(self.data['gap_matrix'])
            torsion_proxy = np.std(gap_matrix, axis=0)
            return {
                'avg_torsion': float(np.mean(torsion_proxy[-50:])),
                'torsion_converged': bool(np.all(torsion_proxy[-20:] < 0.3)),
                'max_torsion': float(np.max(torsion_proxy))
            }
        return {'avg_torsion': None, 'torsion_converged': None, 'max_torsion': None}

    def generate_plots(self, pdf_path: str):
        with PdfPages(pdf_path) as pdf:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(self.data['step_energies'], label='Energia Média (GeV)', linewidth=2)
            ax.axhline(self.meta.kolmogorov_limit, color='red', linestyle='--',
                      label=f'Limiar Kolmogorov ({self.meta.kolmogorov_limit} GeV)')
            ax.set_xlabel('Passo'); ax.set_ylabel('Energia (GeV)')
            ax.legend(); ax.grid(True, alpha=0.3)
            ax.set_title('Convergência da Aceleração')
            pdf.savefig(fig); plt.close(fig)

            fig, ax1 = plt.subplots(figsize=(10, 4))
            ax1.plot(self.data['step_gaps'], color='orange', label='ΔK médio')
            ax1.set_ylabel('Gap Kolmogorov', color='orange')
            ax2 = ax1.twinx()
            if 'avg_priority' in self.data:
                ax2.plot(self.data['avg_priority'], color='green', label='Prioridade Π')
                ax2.set_ylabel('Prioridade', color='green')
            ax1.set_xlabel('Passo'); ax1.grid(True, alpha=0.3)
            ax1.set_title('Coerência e Prioridade')
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1+lines2, labels1+labels2)
            pdf.savefig(fig); plt.close(fig)

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
            ax1.plot(self.data['sf_history'], color='purple', label='Spreading Factor')
            ax1.set_ylabel('SF'); ax1.set_ylim(6, 13); ax1.grid(True, alpha=0.3)
            ax2.plot(self.data['tx_interval_history'], color='brown', label='Intervalo TX (s)')
            ax2.set_ylabel('Intervalo (s)'); ax2.set_xlabel('Passo'); ax2.grid(True, alpha=0.3)
            fig.suptitle('Calibração Adaptativa LoRa')
            pdf.savefig(fig); plt.close(fig)

            if 'gap_matrix' in self.data:
                gap_matrix = np.array(self.data['gap_matrix'])
                torsion = np.std(gap_matrix, axis=0)
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(torsion, label='Torção (std espacial dos gaps)')
                ax.axhline(0.3, color='red', linestyle=':', label='Limiar de convergência')
                ax.set_xlabel('Passo'); ax.set_ylabel('Torção')
                ax.legend(); ax.grid(True, alpha=0.3)
                ax.set_title('Evolução da Torção da Rede')
                pdf.savefig(fig); plt.close(fig)

    def generate_html_report(self, metrics: Dict, pdf_path: str) -> str:
        signature = self.meta.sign("ARKHE_ORCHESTRATOR_PRIVATE_KEY_PLACEHOLDER")
        val = metrics.get("validation", {})
        gap_stat = val.get("gap_stationarity", {})

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>ARKHE OS v158 — Relatório de Desempenho</title>
</head>
<body>
    <h1>🌍 ARKHE OS v158 — Relatório de Desempenho</h1>
    <p><strong>Report ID:</strong> <code>{self.report_id}</code></p>

    <h2>1. 🎯 Convergência</h2>
    <ul>
        <li>Energia final: {metrics['convergence']['final_energy']:.2f} GeV</li>
        <li>Limiar alcançado: {metrics['convergence']['kolmogorov_reached']}</li>
    </ul>

    <h2>2. 📊 Validação Estatística</h2>
    <ul>
        <li>Estacionário: {gap_stat.get('is_stationary', False)} (p={gap_stat.get('p_value', 1.0):.3f})</li>
    </ul>

    <div class="signature"><code>{signature}</code></div>
</body>
</html>"""
        html_path = f"report_{self.report_id}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return html_path

    def run(self, output_dir: str = ".") -> Dict:
        import os
        os.makedirs(output_dir, exist_ok=True)
        metrics = {
            'convergence': self.convergence_metrics(),
            'coherence': self.coherence_analysis(),
            'efficiency': self.network_efficiency(),
            'torsion': self.torsion_metrics()
        }

        if 'step_gaps' in self.data and 'step_energies' in self.data:
            from convergence_validation import verify_convergence
            metrics['validation'] = verify_convergence(
                np.array(self.data['step_gaps']),
                np.array(self.data['step_energies']),
                self.meta.kolmogorov_limit
            )

        pdf_path = os.path.join(output_dir, f"report_{self.report_id}.pdf")
        self.generate_plots(pdf_path)
        html_path = self.generate_html_report(metrics, pdf_path)
        return metrics
