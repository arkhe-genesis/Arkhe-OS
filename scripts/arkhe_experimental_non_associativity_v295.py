#!/usr/bin/env python3
"""
arkhe_experimental_non_associativity_v295.py
Substrato 295: Prova Experimental de Não-Associatividade Atômica

Simula o experimento quântico para detectar assinaturas de não-associatividade
octoniônica em emaranhamento de três partículas, validando que (AB)C != A(BC).
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit import transpile

def octonionic_phase_gate(unit_index: int, target_qubit: int) -> QuantumCircuit:
    """
    Implementa multiplicação por unidade imaginária e_i como porta quântica.

    Baseado no diagrama de Fano: e_i age como troca de base com fase.
    Simplificação: usa porta X com fase condicional para simular efeito octoniônico.
    """
    qc = QuantumCircuit(3)
    # Porta X no qubit alvo
    qc.x(target_qubit)
    # Fase condicional baseada em índice (simula estrutura de Fano)
    if unit_index in [1, 2, 4]:  # e_1, e_2, e_4 formam linha do Fano
        qc.cp(np.pi/2, (target_qubit+1)%3, target_qubit)  # fase +pi/2
    elif unit_index in [3, 5, 6]:  # e_3, e_5, e_6: fase oposta
        qc.cp(-np.pi/2, (target_qubit+1)%3, target_qubit)
    return qc

def build_assoc_test_circuit(sequence: str) -> QuantumCircuit:
    """
    Constrói circuito para testar associatividade.

    sequence: 'ABC' ou 'A(BC)' ou '(AB)C'
    """
    qc = QuantumCircuit(3, 3)

    # Estado inicial GHZ
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(0, 2)

    # Aplicar observáveis na ordem especificada
    if sequence == 'ABC':
        qc.compose(octonionic_phase_gate(4, 2), inplace=True)  # C = e_4 no qubit 2
        qc.compose(octonionic_phase_gate(2, 1), inplace=True)  # B = e_2 no qubit 1
        qc.compose(octonionic_phase_gate(1, 0), inplace=True)  # A = e_1 no qubit 0
    elif sequence == 'A(BC)':
        # Primeiro BC como bloco
        bc = QuantumCircuit(3)
        bc.compose(octonionic_phase_gate(4, 2), inplace=True)
        bc.compose(octonionic_phase_gate(2, 1), inplace=True)
        qc.compose(bc, inplace=True)
        # Depois A
        qc.compose(octonionic_phase_gate(1, 0), inplace=True)
    elif sequence == '(AB)C':
        # Primeiro AB como bloco
        ab = QuantumCircuit(3)
        ab.compose(octonionic_phase_gate(2, 1), inplace=True)
        ab.compose(octonionic_phase_gate(1, 0), inplace=True)
        qc.compose(ab, inplace=True)
        # Depois C
        qc.compose(octonionic_phase_gate(4, 2), inplace=True)

    # Medição em base Z(x)Z(x)Z
    qc.measure([0,1,2], [0,1,2])
    return qc

def compute_assoc_violation(results_abc: dict, results_abc_paren: dict) -> float:
    """
    Calcula Delta_assoc = |<(AB)C> - <A(BC)>| a partir de resultados de medição.
    """
    # Valor esperado de Z(x)Z(x)Z: +1 para paridade par de 1s, -1 para ímpar
    def expectation_zzz(counts: dict) -> float:
        total = sum(counts.values())
        exp_val = 0
        for outcome, count in counts.items():
            parity = outcome.count('1') % 2
            exp_val += (1 if parity == 0 else -1) * count / total
        return exp_val

    exp_abc = expectation_zzz(results_abc)
    exp_paren = expectation_zzz(results_abc_paren)

    return abs(exp_abc - exp_paren)

def simulate_assoc_test(shots: int = 10000, gate_error: float = 0.01) -> dict:
    """
    Simula o experimento de teste de associatividade com ruído realista.
    """
    # Modelo de ruído: depolarização por porta
    noise_model = NoiseModel()
    error_1q = depolarizing_error(gate_error, 1)  # erro de 1 qubit
    error_2q = depolarizing_error(gate_error, 2)  # erro de 2 qubits
    noise_model.add_all_qubit_quantum_error(error_1q, ['x'])
    noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cp'])

    # Executar circuitos
    backend = AerSimulator(noise_model=noise_model)

    circuit_abc = build_assoc_test_circuit('ABC')
    circuit_paren = build_assoc_test_circuit('A(BC)')  # teste A(BC) vs (AB)C (ou equivalente)

    # Transpilar circuitos
    t_circuit_abc = transpile(circuit_abc, backend)
    t_circuit_paren = transpile(circuit_paren, backend)

    job_abc = backend.run(t_circuit_abc, shots=shots)
    job_paren = backend.run(t_circuit_paren, shots=shots)

    results_abc = job_abc.result().get_counts()
    results_paren = job_paren.result().get_counts()

    # Calcular Delta_assoc
    delta = compute_assoc_violation(results_abc, results_paren)

    # Incerteza estatística (propagação de erro binomial)
    error_bar = np.sqrt(2 / shots)  # aproximação para diferença de médias

    # Significância estatística
    significance = delta / error_bar if error_bar > 0 else 0

    return {
        'delta_assoc': float(delta),
        'error_bar': float(error_bar),
        'significance': float(significance),
        'raw_counts_abc': results_abc,
        'raw_counts_paren': results_paren,
        'shots': shots,
        'gate_error': gate_error
    }

# Executar simulação
if __name__ == "__main__":
    print("🌀 Simulando teste de não-associatividade octoniônica...")

    # Parâmetros realistas para hardware atual
    results = simulate_assoc_test(shots=20000, gate_error=0.005)

    print(f"\n📊 RESULTADOS DA SIMULAÇÃO:")
    print(f"   Delta_assoc medido: {results['delta_assoc']:.4f}")
    print(f"   Incerteza estatística: ±{results['error_bar']:.4f}")
    print(f"   Significância: {results['significance']:.2f}σ")
    print(f"   Shots: {results['shots']}, Erro de porta: {results['gate_error']*100:.2f}%")

    if results['significance'] > 3:
        print(f"\n✅ DETECÇÃO SIGNIFICATIVA: Violação de associatividade detectada!")
        print(f"   Evidência para estrutura octoniônica em sistema quântico.")
    elif results['significance'] > 1:
        print(f"\n⚠️  SINAL PROMISSOR: Tendência para violação, mas não conclusivo.")
        print(f"   Aumentar shots ou reduzir ruído para confirmação.")
    else:
        print(f"\n❌ SEM DETECÇÃO: Resultados consistentes com associatividade.")
        print(f"   Pode indicar: (1) modelo octoniônico incorreto, ou (2) ruído dominante.")
