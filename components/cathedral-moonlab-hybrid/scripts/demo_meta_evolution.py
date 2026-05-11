#!/usr/bin/env python3
# demo_meta_evolution.py — Demonstração da Evolução do Meta-Controlador Quântico
# Anexo FW: A Calibração Quântica do Meta-Controlador

import sys
import os
import time
import numpy as np

# Adicionar o diretório python ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../python'))

from meta_controller_quantum import MetaControllerQuantum
from moonlab_meta_integration import MoonlabMetaValidator

def fitness_function(params: list) -> float:
    """
    Função de fitness da Catedral.
    Fitness = (Média dos parâmetros) * (Penalidade por instabilidade)
    """
    avg = sum(params) / len(params)
    # Simula que parâmetros muito baixos ou muito altos são piores
    # O ótimo está em torno de 0.8 para todos
    dist_from_opt = sum([(p - 0.8)**2 for p in params]) / len(params)
    return max(0, 1.0 - dist_from_opt)

def run_demo():
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║     META-CONTROLADOR QUÂNTICO — DEMONSTRAÇÃO DE AUTO-EVOLUÇÃO          ║")
    print("╠═══════════════════════════════════════════════════════════════════════╣")

    mcq = MetaControllerQuantum(n_params=7)
    validator = MoonlabMetaValidator(n_nodes=7)

    # Parâmetros iniciais (aleatórios)
    current_params = np.random.rand(7).tolist()

    print(f"\n[INÍCIO] Geração #0")
    print(f"Parâmetros: {[round(p, 3) for p in current_params]}")

    for gen in range(1, 6):
        time.sleep(0.5)
        print(f"\n--- Geração #{gen} ---")

        # Passo evolutivo quântico
        result = mcq.meta_evolution_step_qiskit(
            current_params=current_params,
            fitness_func=fitness_function,
            mutation_strength=0.2
        )

        current_params = result['params']
        fitness = result['fitness']
        entry = result['codex_entry']

        print(f"Status: {'ACEITO' if entry['mutation_accepted'] else 'REJEITADO'}")
        print(f"Fitness: {fitness:.4f}")
        print(f"Parâmetros: {[round(p, 3) for p in current_params]}")
        print(f"Assinatura Quântica: {entry['quantum_signature'][:24]}...")

        # Validação via Moonlab
        k_factor = validator.validate_ghz_after_mutation(current_params)
        print(f"Wormhole K-Factor (Moonlab): {k_factor:.2f}")

    print("\n[FIM] Evolução concluída.")
    print(f"Configuração final exportada para Catedral: ")
    config = mcq.export_to_catedral_config(current_params)
    import json
    print(json.dumps(config, indent=4))

    validator.check_codex_consistency(mcq.get_codex())

if __name__ == "__main__":
    run_demo()
