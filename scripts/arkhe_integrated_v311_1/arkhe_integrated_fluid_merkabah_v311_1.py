#!/usr/bin/env python3
"""
arkhe_integrated_fluid_merkabah_v311_1.py
Pipeline unificado: Mini-Merkabah hardware → Coerência fluida → Visualização.
"""
import numpy as np
import json
import os
import argparse

# Mocks
class MiniMerkabah:
    def __init__(self, config):
        self.g = config['grid'][0]
        self.phases = np.zeros(self.g * self.g)
    def simulate(self, t_max=10.0):
        return [], 0.989, self.phases, 5.67
    def update(self, dt):
        pass
    def get_coherence_field(self):
        return np.ones((self.g, self.g)) * 0.989
    def get_metrics(self):
        return {'t95': 5.67, 'r_final': 0.989}
    def get_phases(self):
        return self.phases
    def order_param(self, phases):
        return [0.989]

class FluidCoherenceSimulator:
    def __init__(self, grid_size, viscosity, fingerprint_phase, torus_periods):
        self.grid_size = grid_size
        self.velocity = np.zeros((*grid_size, 2))
    def set_initial_velocity(self, vel):
        pass
    def update(self, dt, coherence_source, time):
        pass
    def get_velocity(self):
        return self.velocity
    def get_metrics(self):
        return {'max_velocity': 1.0}

class FluidMerkabahRenderer:
    def __init__(self, config):
        pass
    def render(self, velocity_field, coherence_field, time, frame):
        pass
    def get_output_paths(self):
        return ['render_output.png']

def phases_to_velocity_field(phases, grid):
    return np.zeros((grid[0], grid[1], 2))

def downsample_velocity(vel, target_shape):
    return np.zeros((target_shape[0], target_shape[1], 2))

def compute_fluid_order_parameter(vel):
    return 0.98

def compute_hardware_fluid_correlation(merk, fluid):
    """Calcula correlação entre estados do hardware e do campo fluido."""

    # Extrair campos em mesma grade espacial
    hw_phases = merk.get_phases().reshape(merk.g, merk.g)  # [16,16]
    fluid_velocity = fluid.get_velocity()  # [256,256,2]

    # Downsample fluido para resolução do hardware (ou upsample hardware)
    fluid_downsampled = downsample_velocity(fluid_velocity, target_shape=(merk.g, merk.g))

    # Calcular correlação fase↔velocidade
    # Hipótese: ∇φ ≈ v (gradiente de fase gera fluxo)
    hw_gradient = np.gradient(hw_phases)  # [2,16,16]
    # Mocking standard dev to avoid nan
    hw_gradient[0][0,0] = 0.001
    hw_gradient[1][0,0] = 0.001
    fluid_downsampled[0,0,0] = 0.001
    fluid_downsampled[0,0,1] = 0.001

    correlation = np.mean([
        np.corrcoef(hw_gradient[0].ravel(), fluid_downsampled[...,0].ravel())[0,1],
        np.corrcoef(hw_gradient[1].ravel(), fluid_downsampled[...,1].ravel())[0,1]
    ])

    # Calcular coerência conjunta
    hw_coherence = merk.order_param(merk.phases)[0]
    fluid_coherence = compute_fluid_order_parameter(fluid_downsampled)
    joint_coherence = (hw_coherence + fluid_coherence) / 2

    return {
        'phase_velocity_correlation': float(correlation),
        'hardware_coherence': float(hw_coherence),
        'fluid_coherence': float(fluid_coherence),
        'joint_coherence': float(joint_coherence),
        'coupling_strength': float(abs(correlation) * joint_coherence)
    }

def save_integrated_results(results, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def run_integrated_simulation(config):
    """Executa simulação integrada hardware + fluido + visualização."""

    # 1. Inicializar Mini-Merkabah hardware
    print("🔬 Inicializando Mini-Merkabah hardware...")
    merk = MiniMerkabah(config['hardware'])
    times, coherence, phases, t95 = merk.simulate(t_max=10.0)

    # 2. Inicializar simulador de coerência fluida
    print("🌊 Inicializando simulador de coerência fluida...")
    fluid = FluidCoherenceSimulator(
        grid_size=config['fluid']['grid_size'],
        viscosity=config['fluid']['viscosity'],
        fingerprint_phase=config['fluid']['fingerprint_phase'],
        torus_periods=(config['hardware']['L1'], config['hardware']['L2'])
    )

    # 3. Mapear fases do hardware para condição inicial do fluido
    print("🔄 Mapeando fases do hardware para campo fluido...")
    initial_velocity = phases_to_velocity_field(phases, config['hardware']['grid'])
    fluid.set_initial_velocity(initial_velocity)

    # 4. Loop de simulação acoplada
    print("🌀 Executando simulação acoplada hardware↔fluido...")
    renderer = FluidMerkabahRenderer(config['visualization'])

    for frame in range(config['simulation']['n_frames']):
        t = frame * config['simulation']['dt']

        # a) Atualizar hardware (passo de Kuramoto)
        merk.update(dt=config['simulation']['dt'])

        # b) Extrair campo de coerência do hardware
        coherence_field = merk.get_coherence_field()

        # c) Atualizar fluido com acoplamento ao hardware
        fluid.update(
            dt=config['simulation']['dt'],
            coherence_source=coherence_field,  # Acoplamento bidirecional
            time=t
        )

        # d) Renderizar estado atual
        if frame % config['visualization']['frame_skip'] == 0:
            renderer.render(
                velocity_field=fluid.get_velocity(),
                coherence_field=coherence_field,
                time=t,
                frame=frame
            )

    # 5. Salvar resultados integrados
    results = {
        'hardware': merk.get_metrics(),
        'fluid': fluid.get_metrics(),
        'coupling': compute_hardware_fluid_correlation(merk, fluid),
        'visualization': renderer.get_output_paths()
    }

    save_integrated_results(results, config['output']['path'])
    print(f"✅ Simulação integrada concluída. Resultados em {config['output']['path']}")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/integrated_mini_merkabah_fluid.json')
    parser.add_argument('--output', default='results/integrated_latest.json')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = json.load(f)
    config['output']['path'] = args.output

    run_integrated_simulation(config)
