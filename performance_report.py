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
        """Assina o relatório com chave do orchestrator."""
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

        # Passo de cruzamento do limiar
        threshold_idx = np.argmax(energies >= limit)
        threshold_step = threshold_idx if energies[threshold_idx] >= limit else None

        # Taxa de convergência (ajuste exponencial na cauda)
        tail_start = int(0.7 * len(energies))
        if len(energies) - tail_start > 20:
            t = np.arange(tail_start, len(energies))
            e_tail = np.clip(limit - energies[tail_start:], 1e-6, None)
            log_diff = np.log(e_tail)
            slope, _ = np.polyfit(t, log_diff, 1)
            conv_rate = -slope
        else:
            conv_rate = None

        return {
            'threshold_step': int(threshold_step) if threshold_step is not None else None,
            'convergence_rate': float(conv_rate) if conv_rate else None,
            'final_energy': float(energies[-1]),
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
        """Eficiência energética: aceleração total / energia consumida."""
        intervals = np.array(self.data['tx_interval_history'])
        sf_vals = np.array(self.data['sf_history'])

        # Modelo de consumo LoRa simplificado
        bw = 250e3  # Hz
        payload_bits = 24 * 8
        cr = 1.25  # 4/5 coding rate
        t_air = payload_bits * cr * (2.0 ** sf_vals) / bw  # segundos
        p_tx_base = 0.1  # Watts (14 dBm)
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
        """Métrica de torção: desvio espacial dos gaps."""
        if 'gap_matrix' in self.data:
            gap_matrix = np.array(self.data['gap_matrix'])  # (nodes, steps)
            torsion_proxy = np.std(gap_matrix, axis=0)
            return {
                'avg_torsion': float(np.mean(torsion_proxy[-50:])),
                'torsion_converged': bool(np.all(torsion_proxy[-20:] < 0.3)),
                'max_torsion': float(np.max(torsion_proxy))
            }
        return {'avg_torsion': None, 'torsion_converged': None, 'max_torsion': None}

    def generate_plots(self, pdf_path: str):
        """Gera figuras e salva em PDF."""
        with PdfPages(pdf_path) as pdf:
            # Figura 1: Energia e limiar
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(self.data['step_energies'], label='Energia Média (GeV)', linewidth=2)
            ax.axhline(self.meta.kolmogorov_limit, color='red', linestyle='--',
                      label=f'Limiar Kolmogorov ({self.meta.kolmogorov_limit} GeV)')
            ax.set_xlabel('Passo'); ax.set_ylabel('Energia (GeV)')
            ax.legend(); ax.grid(True, alpha=0.3)
            ax.set_title('Convergência da Aceleração')
            pdf.savefig(fig); plt.close(fig)

            # Figura 2: Gap e prioridade
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

            # Figura 3: Parâmetros LoRa adaptativos
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
            ax1.plot(self.data['sf_history'], color='purple', label='Spreading Factor')
            ax1.set_ylabel('SF'); ax1.set_ylim(6, 13); ax1.grid(True, alpha=0.3)
            ax2.plot(self.data['tx_interval_history'], color='brown', label='Intervalo TX (s)')
            ax2.set_ylabel('Intervalo (s)'); ax2.set_xlabel('Passo'); ax2.grid(True, alpha=0.3)
            fig.suptitle('Calibração Adaptativa LoRa')
            pdf.savefig(fig); plt.close(fig)

            # Figura 4: Torção (se disponível)
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
        """Gera relatório HTML com métricas e links para PDF."""
        signature = self.meta.sign("ARKHE_ORCHESTRATOR_PRIVATE_KEY_PLACEHOLDER")

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>ARKHE OS v158 — Relatório de Desempenho</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #0a0e17; color: #e0e6f0; }}
        h1 {{ color: #7dd3fc; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }}
        h2 {{ color: #a78bfa; margin-top: 30px; }}
        .metric {{ background: #1e293b; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .metric-value {{ font-size: 1.4em; color: #22d3ee; font-weight: bold; }}
        .success {{ color: #4ade80; }} .warning {{ color: #fbbf24; }} .error {{ color: #f87171; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #1e293b; color: #94a3b8; }}
        .signature {{ font-family: monospace; font-size: 0.9em; color: #64748b; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>🌍 ARKHE OS v158 — Relatório de Desempenho da Rede de Coerência</h1>
    <p><strong>Report ID:</strong> <code>{self.report_id}</code> |
       <strong>Gerado em:</strong> {self.meta.simulation_timestamp}</p>

    <h2>1. 🎯 Convergência da Aceleração</h2>
    <div class="metric">
        <div>Limiar de Kolmogorov: <span class="metric-value">{self.meta.kolmogorov_limit} GeV</span></div>
        <div>Atingido: <span class="{'success' if metrics['convergence']['kolmogorov_reached'] else 'error'}">
            {'✓ Sim' if metrics['convergence']['kolmogorov_reached'] else '✗ Não'}
        </span></div>
        <div>Passo do limiar: <span class="metric-value">{metrics['convergence']['threshold_step'] or 'N/A'}</span></div>
            <div>Taxa de convergência: <span class="metric-value">{metrics['convergence']['convergence_rate']:.4f} por passo</span></div>
        <div>Energia final: <span class="metric-value">{metrics['convergence']['final_energy']:.2f} GeV</span></div>
    </div>

    <h2>2. 🔗 Coerência e Gap Kolmogorov</h2>
    <div class="metric">
        <div>Gap médio final: <span class="metric-value">{metrics['coherence']['final_avg_gap']:.3f}</span></div>
        <div>Desvio padrão (últimos 100 passos): <span class="metric-value">{metrics['coherence']['gap_std_final']:.3f}</span></div>
        <div>Tendência do gap: <span class="{'success' if metrics['coherence']['gap_trend_slope'] < 0 else 'warning'}">
            {'↓ Decrescente' if metrics['coherence']['gap_trend_slope'] < 0 else '→ Estável/Crescente'}
        </span> (slope={metrics['coherence']['gap_trend_slope']:.4f})</div>
    </div>

    <h2>3. ⚡ Eficiência da Rede LoRa</h2>
    <div class="metric">
        <div>Potência total estimada: <span class="metric-value">{metrics['efficiency']['avg_power_W']:.3f} W</span></div>
        <div>Energia consumida: <span class="metric-value">{metrics['efficiency']['total_energy_J']:.2f} J</span></div>
        <div>Aceleração por joule: <span class="metric-value">{metrics['efficiency']['acceleration_per_joule']:.4f} GeV/J</span></div>
        <div>Tempo no ar médio: <span class="metric-value">{metrics['efficiency']['avg_airtime_ms']:.1f} ms</span></div>
    </div>

    <h2>4. 🌀 Torção e Inteligência da Rede</h2>
    <div class="metric">
        <div>Torção média (final): <span class="metric-value">{metrics['torsion']['avg_torsion'] if metrics['torsion']['avg_torsion'] is not None else 'N/D'}</span></div>
        <div>Torção convergiu: <span class="{'success' if metrics['torsion']['torsion_converged'] else 'warning'}">
            {'✓ Sim' if metrics['torsion']['torsion_converged'] else '✗ Não / Não avaliado'}
        </span></div>
    </div>

    <h2>5. 📊 Validação Estatística</h2>
    <table>
        <tr><th>Métrica</th><th>Valor</th><th>Limiar</th><th>Status</th></tr>
        <tr><td>Estacionariedade do gap (ADF)</td>
            <td>p={metrics.get('validation', {}).get('gap_stationarity', {}).get('p_value', 1.0):.3f}</td>
            <td>p &lt; 0.05</td>
            <td class="{'success' if metrics.get('validation', {}).get('gap_stationarity', {}).get('is_stationary', False) else 'warning'}">
                {'✓ Estacionário' if metrics.get('validation', {}).get('gap_stationarity', {}).get('is_stationary', False) else '⚠ Não estacionário'}
            </td></tr>
        <tr><td>Tendência decrescente do gap</td>
            <td>slope={metrics['coherence']['gap_trend_slope']:.4f}</td>
            <td>slope &lt; 0</td>
            <td class="{'success' if metrics['coherence']['gap_trend_slope'] < 0 else 'warning'}">
                {'✓ Decrescente' if metrics['coherence']['gap_trend_slope'] < 0 else '⚠ Não decrescente'}
            </td></tr>
        <tr><td>Limiar Kolmogorov (IC 95%)</td>
                <td>[{metrics.get('convergence', {}).get('final_energy_ci', (0.0, 0.0))[0]:.2f}, {metrics.get('convergence', {}).get('final_energy_ci', (0.0, 0.0))[1]:.2f}] GeV</td>
            <td>&gt;= {self.meta.kolmogorov_limit} GeV</td>
            <td class="{'success' if metrics['convergence']['kolmogorov_reached'] else 'error'}">
                {'✓ Atingido' if metrics['convergence']['kolmogorov_reached'] else '✗ Não atingido'}
            </td></tr>
    </table>

    <h2>6. 📎 Anexos</h2>
    <p>Gráficos completos em PDF: <a href="{pdf_path}" style="color:#7dd3fc">{pdf_path}</a></p>

    <div class="signature">
        <p><strong>Assinatura do Relatório:</strong><br>
        <code>{signature}</code></p>
        <p><em>Relatório gerado automaticamente pelo ARKHE Orchestrator v158.
        Para verificar a integridade, compare o hash com o registrado no ledger Arxia.</em></p>
    </div>
</body>
</html>"""
        html_path = f"report_{self.report_id}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return html_path

    def run(self, output_dir: str = ".") -> Dict:
        """Executa geração completa do relatório."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Calcular métricas
        metrics = {
            'convergence': self.convergence_metrics(),
            'coherence': self.coherence_analysis(),
            'efficiency': self.network_efficiency(),
            'torsion': self.torsion_metrics()
        }

        # Adicionar validação estatística se disponível
        if 'step_gaps' in self.data and 'step_energies' in self.data:
            from convergence_validation import verify_convergence
            metrics['validation'] = verify_convergence(
                np.array(self.data['step_gaps']),
                np.array(self.data['step_energies']),
                self.meta.kolmogorov_limit
            )

        # Gerar PDF e HTML
        pdf_path = os.path.join(output_dir, f"report_{self.report_id}.pdf")
        self.generate_plots(pdf_path)
        html_path = self.generate_html_report(metrics, pdf_path)

        print(f"✅ Relatório gerado: {html_path}")
        print(f"📊 Gráficos: {pdf_path}")
        return metrics
