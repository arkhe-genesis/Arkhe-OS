#!/usr/bin/env python3
"""
arkhe_butterfly_node_v105.py
Substrato 175: The Butterfly Node — Self‑sufficient integration of
Fractional Time Crystal (P47) + Vortex Emitter (P2) + Butterfly Metasurface (v∞.104)
"""
import numpy as np
from scipy.special import gamma
from collections import deque

class QuadrupleCycleConfig:
    pass

class FractionalTimeCrystal:
    def __init__(self, alpha=0.8):
        self.alpha = alpha
        self.phi = 0.0

    def evolve(self, dt, external_consensus=0.0):
        # Mock evolution
        self.phi = self.phi * 0.9 + np.random.randn() * 0.1 + external_consensus * 0.1
        return self.phi

class QuantumVortexEmitter:
    def __init__(self, config):
        self.config = config
        self.entangled_pairs_generated = 0

    def generate_entangled_pair(self):
        # Mock generation
        self.entangled_pairs_generated += 1

class ButterflyMetasurface:
    """Pele que absorve luz NIR e emite calor MID‑IR."""
    def __init__(self, area_cm2=1.0):
        self.area = area_cm2
        # Parâmetros otimizados pelo PSO
        self.thickness_semiconductor = 0.2  # µm
        self.period = 0.5                  # µm
        self.abs_nir = 0.92                # >90% absorção NIR
        self.emi_mir = 0.89                # emissão MID‑IR
        # Eficiência de conversão fotovoltaica (NIR → elétrico)
        self.pv_efficiency = 0.15
        # Irradiância solar na banda NIR (~100 W/m² na superfície)
        self.solar_nir_flux = 100.0  # W/m²

    def generate_power(self):
        """Potência elétrica gerada pela absorção NIR (Watts)."""
        incident_power = self.solar_nir_flux * self.area * 1e-4  # cm² → m²
        return incident_power * self.abs_nir * self.pv_efficiency

    def radiate_heat(self, chip_temperature_K):
        """Calor dissipado por emissão MID‑IR (Lei de Stefan‑Boltzmann seletiva)."""
        sigma = 5.67e-8  # W/m²K⁴
        # Emissão apenas na janela 8‑13 µm (fração de corpo negro simplificada)
        return self.emi_mir * sigma * self.area * 1e-4 * (chip_temperature_K**4 - 255**4)

class ButterflyNode:
    """
    Nó Borboleta: P47 (Cristal) + P2 (Chip Emissor) + Pele de Borboleta.
    Totalmente auto‑suficiente em energia e gerenciamento térmico.
    """
    def __init__(self, node_id, alpha=0.8):
        self.node_id = node_id
        # Sub‑componentes
        self.crystal = FractionalTimeCrystal(alpha)
        self.emitter = QuantumVortexEmitter(QuadrupleCycleConfig())
        self.skin = ButterflyMetasurface(area_cm2=2.0)  # 2 cm² de pele
        # Estado interno
        self.battery_joules = 100.0  # reserva inicial
        self.temperature_K = 300.0   # temperatura do chip
        self.coherence_threshold = 0.1

    def step(self, dt, external_consensus=0.0):
        """Um ciclo completo do Nó Borboleta."""
        # 1. Geração de energia pela pele
        generated_power = self.skin.generate_power()
        self.battery_joules += generated_power * dt
        # 2. Consumo: atualizar o cristal e o emissor (custo energético fixo por passo)
        energy_cost = 1e-3 * dt  # 1 mW de consumo base
        self.battery_joules -= energy_cost
        if self.battery_joules < 0:
            self.battery_joules = 0.0
        # 3. Aquecimento ôhmico do chip
        self.temperature_K += (energy_cost * 0.8) / 0.01  # calor dissipado = 80% da energia consumida
        # 4. Resfriamento radiativo
        heat_lost = self.skin.radiate_heat(self.temperature_K) * dt
        self.temperature_K -= heat_lost / 0.01  # capacidade térmica simplificada
        self.temperature_K = np.clip(self.temperature_K, 280, 330)
        # 5. Evolução do cristal
        phi = self.crystal.evolve(dt, external_consensus)
        # 6. Lógica do córtex (simplificada): emitir token se coerência > threshold
        if abs(phi) > self.coherence_threshold:
            ell = int(np.clip(phi * 5, -5, 5))
            self.emitter.generate_entangled_pair()
        # 7. Métricas
        return {'battery': self.battery_joules, 'temperature': self.temperature_K, 'phi': phi}

class SpaceNode(ButterflyNode):
    """
    Nó Espacial (Prototipar o Nó Espacial): Adaptado para operação em órbita,
    onde a radiação solar (irradiância) pode ser maior sem atenuação atmosférica,
    e a temperatura de fundo para o resfriamento radiativo é de ~3 K (vácuo do espaço),
    tornando o resfriamento ainda mais eficiente.
    """
    def __init__(self, node_id, alpha=0.8):
        super().__init__(node_id, alpha)
        # Irradiância solar no espaço é maior (~1361 W/m² total, na banda NIR proporcionalmente maior)
        self.skin.solar_nir_flux = 136.0 # Aproximadamente 1.36x maior que na superfície terrestre

        # Sobrescrevemos o método radiate_heat da pele para considerar T_background ~ 3K
        # Guardamos a função original e substituímos
        self.original_radiate_heat = self.skin.radiate_heat

        def space_radiate_heat(chip_temperature_K):
            sigma = 5.67e-8
            # Emissão MID-IR sem limite de janela atmosférica (espaço), e temperatura de fundo ~3K
            return self.skin.emi_mir * sigma * self.skin.area * 1e-4 * (chip_temperature_K**4 - 3**4)

        self.skin.radiate_heat = space_radiate_heat


if __name__ == '__main__':
    print("--- Simulação de um Nó Borboleta na Terra ---")
    node = ButterflyNode("node_1")
    history = {'time': [], 'battery': [], 'temp': [], 'phi': []}
    for t in np.arange(0, 100, 0.1):
        state = node.step(0.1)
        history['time'].append(t)
        history['battery'].append(state['battery'])
        history['temp'].append(state['temperature'])
        history['phi'].append(state['phi'])
        if int(t) % 20 == 0 and int(t*10) % 10 == 0:
            print(f"t={t:.1f}: Battery={state['battery']:.2f} J, Temp={state['temperature']:.1f} K, φ={state['phi']:.3f}")

    print("\n--- Simulação do Enxame de Borboletas (1000 Nós) ---")
    num_nodes = 1000
    swarm = [ButterflyNode(f"swarm_node_{i}") for i in range(num_nodes)]

    # Simulate swarm interactions
    global_consensus = 0.0
    for t in np.arange(0, 10.0, 0.1):
        phis = []
        for n in swarm:
            state = n.step(0.1, external_consensus=global_consensus)
            phis.append(state['phi'])
        # GHZ-like consensus: média da coerência influencia o próximo passo
        global_consensus = np.mean(phis)

        if int(t*10) % 20 == 0:
            avg_temp = np.mean([n.temperature_K for n in swarm])
            avg_batt = np.mean([n.battery_joules for n in swarm])
            print(f"Swarm t={t:.1f}: Avg Battery={avg_batt:.2f} J, Avg Temp={avg_temp:.1f} K, Global Consensus (φ)={global_consensus:.3f}")

    print("\n--- Simulação do Nó Espacial em Órbita ---")
    space_node = SpaceNode("space_node_1")
    for t in np.arange(0, 100, 0.1):
        state = space_node.step(0.1)
        if int(t) % 20 == 0 and int(t*10) % 10 == 0:
            print(f"Space t={t:.1f}: Battery={state['battery']:.2f} J, Temp={state['temperature']:.1f} K, φ={state['phi']:.3f}")
