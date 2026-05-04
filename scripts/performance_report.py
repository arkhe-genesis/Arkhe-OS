import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import os

class PerformanceReport:
    def __init__(self, sim_data):
        """
        sim_data: dict with keys 'step_energies', 'step_gaps', 'sf_history',
                  'tx_interval_history', 'kolmogorov_limit', 'num_nodes', 'num_electrons'
        """
        self.data = sim_data
        self.report_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def convergence_metrics(self):
        """Calcula métricas de convergência."""
        energies = self.data['step_energies']
        limit = self.data['kolmogorov_limit']
        # Passo em que a energia média atinge o limiar
        threshold_step = np.argmax(np.array(energies) >= limit) if any(np.array(energies) >= limit) else None
        # Taxa de convergência (ajuste exponencial nos últimos 30% dos dados)
        n = len(energies)
        tail = int(0.7 * n)
        if n - tail > 10:
            t = np.arange(tail, n)
            e = np.array(energies[tail:])
            # Ajuste linear do log(limit - energy) -> inclinação = taxa
            with np.errstate(over='ignore'):
                log_diff = np.log(np.maximum(limit - e, 1e-6))
            slope, intercept = np.polyfit(t, log_diff, 1)
            conv_rate = -slope  # positivo se convergindo
        else:
            conv_rate = None
        return {
            'threshold_step': threshold_step,
            'convergence_rate': conv_rate,
            'final_energy': energies[-1],
            'kolmogorov_reached': any(np.array(energies) >= limit)
        }

    def coherence_analysis(self):
        """Analisa a coerência: gap médio final, variância, etc."""
        gaps = self.data['step_gaps']
        return {
            'final_avg_gap': gaps[-1] if len(gaps) > 0 else None,
            'min_gap': min(gaps),
            'max_gap': max(gaps),
            'gap_std': np.std(gaps[-100:]) if len(gaps)>=100 else np.std(gaps)
        }

    def network_efficiency(self):
        """Eficiência energética da rede: aceleração total / (potência consumida média * tempo)."""
        # Potência estimada por nó com base no TX interval e SF médio (modelo simplificado)
        intervals = np.array(self.data['tx_interval_history'])
        sf_vals = np.array(self.data['sf_history'])
        # Consumo por transmissão: P_tx * tempo no ar / intervalo
        # Tempo no ar ~ 24 bytes * 8 * (2**SF) / BW
        bw = 250e3
        payload_bits = 24 * 8
        t_air = payload_bits * (2.0**sf_vals) / bw  # array
        avg_power_per_node = (0.1 * t_air) / np.maximum(intervals, 1)  # Watts (0.1W de potência base)
        total_power = avg_power_per_node.sum()  # soma sobre todos os nós (média temporal final)
        total_steps = len(self.data['step_energies'])
        # Energia total gasta (Joules): potência média * duração total (tempo de simulação)
        # Duração: cada passo = intervalo médio? Vamos aproximar.
        avg_interval = np.mean(intervals)
        total_time = total_steps * avg_interval
        total_energy_consumed = total_power * total_time  # Joules

        # Aceleração total concedida = soma dos incrementos de energia de todos os elétrons
        total_acceleration = (self.data['step_energies'][-1] - self.data['step_energies'][0]) * self.data['num_electrons']  # GeV
        efficiency = total_acceleration / (total_energy_consumed + 1e-9)  # GeV/J
        return {
            'total_power_estimate_W': total_power,
            'total_energy_consumed_J': total_energy_consumed,
            'acceleration_per_joule_GeV_per_J': efficiency
        }

    def torsion_metrics(self):
        """Métrica de torção: gradiente médio de coerência ao longo do tempo."""
        # Na simulação, não guardamos gradiente diretamente; mas podemos reconstruir a partir dos gaps vizinhos?
        # Para o relatório, usaremos o desvio padrão espacial dos gaps como proxy de torção (não uniformidade).
        gaps = np.array(self.data['step_gaps'])
        # Em um sistema sem torção, todos os nós teriam o mesmo gap (consenso perfeito).
        # O desvio padrão entre os nós é uma medida da torção residual.
        # Como a simulação armazenou apenas a média, precisamos modificar a sim para guardar a matriz de gaps.
        # Para este exemplo, assumiremos que a simulação forneceu 'gap_matrix' (N x steps).
        if 'gap_matrix' in self.data:
            gap_matrix = np.array(self.data['gap_matrix'])  # (num_nodes, steps)
            torsion_proxy = np.std(gap_matrix, axis=0)  # std entre nós por passo
            avg_torsion = np.mean(torsion_proxy[-100:])
            torsion_converged = np.all(torsion_proxy[-50:] < 0.5)
        else:
            # Fallback: usar a variância do gap médio como aproximação grosseira
            avg_torsion = None
            torsion_converged = None
        return {
            'avg_torsion_proxy': avg_torsion,
            'torsion_converged': torsion_converged
        }

    def generate_plots(self, save_path=None):
        """Gera figuras e salva em PDF."""
        if save_path is None:
            save_path = f"report_{self.report_time}.pdf"
        with PdfPages(save_path) as pdf:
            fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
            axs[0].plot(self.data['step_energies'], label='Energia Média (GeV)')
            axs[0].axhline(self.data['kolmogorov_limit'], color='r', linestyle='--', label='Limiar Kolmogorov')
            axs[0].set_ylabel('Energia (GeV)')
            axs[0].legend()
            axs[0].grid(True)

            axs[1].plot(self.data['step_gaps'], color='orange', label='ΔK médio')
            axs[1].set_ylabel('ΔK')
            axs[1].legend()
            axs[1].grid(True)

            axs[2].plot(self.data['sf_history'], color='green', label='SF médio')
            axs[2].set_ylabel('SF')
            axs[2].set_ylim(6, 12)
            axs[2].legend()
            axs[2].grid(True)

            axs[3].plot(self.data['tx_interval_history'], color='purple', label='Intervalo TX (s)')
            axs[3].set_ylabel('Intervalo (s)')
            axs[3].set_xlabel('Passo')
            axs[3].legend()
            axs[3].grid(True)

            plt.suptitle('Desempenho da Rede de Coerência ARKHE v157')
            pdf.savefig(fig)
            plt.close(fig)

            # Gráfico de torção (se disponível)
            if 'gap_matrix' in self.data:
                gap_matrix = np.array(self.data['gap_matrix'])
                torsion = np.std(gap_matrix, axis=0)
                fig2, ax = plt.subplots()
                ax.plot(torsion, label='Torção (desvio padrão dos gaps)')
                ax.set_xlabel('Passo')
                ax.set_ylabel('Torção')
                ax.legend()
                ax.grid(True)
                pdf.savefig(fig2)
                plt.close(fig2)

    def generate_html_report(self, metrics, plots_pdf_path):
        """Cria um relatório HTML básico."""
        html = f"""
        <html>
        <head><title>ARKHE OS v157 - Relatório de Desempenho</title></head>
        <body>
            <h1>Relatório de Desempenho da Rede de Coerência</h1>
            <p>Gerado em: {self.report_time}</p>
            <h2>1. Convergência da Aceleração</h2>
            <ul>
                <li><b>Limiar de Kolmogorov:</b> {self.data['kolmogorov_limit']} GeV</li>
                <li><b>Atingido:</b> {'Sim' if metrics['convergence']['kolmogorov_reached'] else 'Não'}</li>
                <li><b>Passo do limiar:</b> {metrics['convergence']['threshold_step']}</li>
                <li><b>Taxa de convergência:</b> {metrics['convergence']['convergence_rate']:.4f} por passo</li>
                <li><b>Energia final:</b> {metrics['convergence']['final_energy']:.2f} GeV</li>
            </ul>
            <h2>2. Coerência</h2>
            <ul>
                <li><b>Gap médio final:</b> {metrics['coherence']['final_avg_gap']:.3f}</li>
                <li><b>Desvio padrão (últimos 100 passos):</b> {metrics['coherence']['gap_std']:.3f}</li>
            </ul>
            <h2>3. Eficiência da Rede</h2>
            <ul>
                <li><b>Potência total estimada:</b> {metrics['efficiency']['total_power_estimate_W']:.3f} W</li>
                <li><b>Energia consumida:</b> {metrics['efficiency']['total_energy_consumed_J']:.2f} J</li>
                <li><b>Aceleração por joule:</b> {metrics['efficiency']['acceleration_per_joule_GeV_per_J']:.4f} GeV/J</li>
            </ul>
            <h2>4. Torção e Inteligência</h2>
            <ul>
                <li><b>Torção média (final):</b> {metrics['torsion']['avg_torsion_proxy'] if metrics['torsion']['avg_torsion_proxy'] is not None else 'N/D'}</li>
                <li><b>Torção convergiu?</b> {'Sim' if metrics['torsion']['torsion_converged'] else 'Não avaliado'}</li>
            </ul>
            <p>Gráficos disponíveis em: <a href="{plots_pdf_path}">{plots_pdf_path}</a></p>
            <hr>
            <p><em>Relatório gerado automaticamente pelo ARKHE Orchestrator v157.</em></p>
        </body>
        </html>
        """
        html_path = f"report_{self.report_time}.html"
        with open(html_path, 'w') as f:
            f.write(html)
        return html_path

    def run(self):
        metrics = {
            'convergence': self.convergence_metrics(),
            'coherence': self.coherence_analysis(),
            'efficiency': self.network_efficiency(),
            'torsion': self.torsion_metrics()
        }
        pdf_path = f"report_{self.report_time}.pdf"
        self.generate_plots(pdf_path)
        html_path = self.generate_html_report(metrics, pdf_path)
        print(f"Relatório gerado: {html_path}")
        return metrics

if __name__ == "__main__":
    # Dados de exemplo (substitua pelos resultados reais da simulação)
    sim_data = {
        'step_energies': np.linspace(0.5, 100, 600),  # placeholder
        'step_gaps': np.linspace(10, 1, 600),
        'sf_history': np.full(600, 8),
        'tx_interval_history': np.full(600, 30),
        'kolmogorov_limit': 100.0,
        'num_nodes': 10,
        'num_electrons': 5
    }
    reporter = PerformanceReport(sim_data)
    reporter.run()
