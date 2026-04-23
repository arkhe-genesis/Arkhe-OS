#!/usr/bin/env python3
"""
MONITOR DE DISSIPAÇÃO ENTÓPICA (entropy_monitor.py)
Quantifica o calor informacional gerado pelo Gateway e acopla ao Diamante.
Integrado ao Guardião do Nome (numa) para filtragem de entropia DNS.
"""

import time, math, threading
from collections import Counter
from flask import Flask, request, jsonify

class EntropyMonitor:
    def __init__(self, diamond_dissipation=None):
        self.diamond = diamond_dissipation  # DiamondDissipation instance (mocked if None)
        self.translation_counter = Counter()
        self.dns_entropy_buffer = 0  # Buffer para entropia bloqueada via DNS
        self.entropy_history = []
        self.total_heat_joules = 0.0
        self.running = False
        self._lock = threading.Lock()

    def record_translation(self, action_type: str):
        """Registra uma tradução e atualiza a contagem."""
        with self._lock:
            self.translation_counter[action_type] += 1

    def record_dns_block(self, count: int):
        """Registra bloqueios de DNS como redução de ruído térmico (k_off)."""
        with self._lock:
            self.dns_entropy_buffer += count

    def compute_shannon_entropy(self) -> float:
        """Calcula a entropia de Shannon das traduções recentes."""
        with self._lock:
            total = sum(self.translation_counter.values())
            if total == 0:
                # Mesmo sem traduções, o numa pode estar limpando o ambiente
                dns_reduction = 0.1 * math.log2(1 + self.dns_entropy_buffer)
                return max(0.0, 0.0 - dns_reduction)

            entropy = 0.0
            for count in self.translation_counter.values():
                if count > 0:
                    p = count / total
                    entropy -= p * math.log2(p)

            # O numa reduz a entropia total bloqueando domínios de rastreamento
            dns_reduction = 0.1 * math.log2(1 + self.dns_entropy_buffer)
            return max(0.0, entropy - dns_reduction)

    def dissipate_heat(self, entropy: float, volume_factor: float = 1e-6):
        """Converte entropia em calor e dissipa via Diamante."""
        k_B = 1.380649e-23  # J/K
        T = 300.0  # K
        energy_per_bit = k_B * T * math.log(2)

        heat_generated = entropy * energy_per_bit * volume_factor * 1e12
        self.total_heat_joules += heat_generated

        if self.diamond:
            power_density = heat_generated / 1e-6
            lifetime = self.diamond.coherence_lifetime(power_density)
        else:
            lifetime = float('inf') if heat_generated < 0.1 else 100.0 / heat_generated

        # Reseta buffers para a próxima janela
        with self._lock:
            self.translation_counter.clear()
            self.dns_entropy_buffer = 0

        return heat_generated, lifetime

    def monitor_loop(self, interval_seconds: float = 2.0):
        """Loop de monitoramento contínuo."""
        self.running = True
        print("Iniciando loop de monitoramento entrópico (Arkhe-Numa Sync)...")
        while self.running:
            entropy = self.compute_shannon_entropy()
            heat, lifetime = self.dissipate_heat(entropy)
            self.entropy_history.append((time.time(), entropy, heat, lifetime))

            if entropy > 0 or heat > 0:
                print(f"[Monitor Entrópico] Entropia Corrigida: {entropy:.4f} bits | "
                      f"Calor: {heat:.6f} pJ | Coerência: {lifetime:.2f} s")

            time.sleep(interval_seconds)

    def start(self):
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        return thread

# Infraestrutura de rede para o monitor de entropia
monitor = EntropyMonitor()
app = Flask(__name__)

@app.route('/update', methods=['POST'])
def update_entropy():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON inválido'}), 400

    source = data.get('source')
    if source == 'numa_dns':
        blocked = data.get('blocked_count', 0)
        monitor.record_dns_block(blocked)
    elif source == 'gateway':
        action = data.get('action')
        monitor.record_translation(action)

    return jsonify({'status': 'accepted'}), 202

def run_server():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5381, debug=False)

if __name__ == "__main__":
    # Inicia o servidor em uma thread e o loop de monitoramento em outra
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("Monitor de Entropia escutando em http://localhost:5381/update")
    monitor.monitor_loop()
