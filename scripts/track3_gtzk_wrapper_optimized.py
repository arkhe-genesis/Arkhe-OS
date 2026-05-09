#!/usr/bin/env python3
"""
track3_gtzk_wrapper_optimized.py
Versão otimizada do wrapper Track 3 com constraints reduzidas.
"""
import numpy as np

def track3_gtzk_instruction_optimized(velocity_fields, pressure_field, grid_size):
    # Otimização 1: Sparse sampling - calcular associador em 1 a cada 4 pontos
    # Otimização 2: L1 norm em vez de L2

    u = np.array(velocity_fields['u'])
    v = np.array(velocity_fields['v'])
    p = np.array(pressure_field)

    # Amostragem esparsa (1 em 4)
    sparse_indices = np.arange(0, len(u), 4)
    u_sparse = u[sparse_indices]
    v_sparse = v[sparse_indices]
    p_sparse = p[sparse_indices]

    # Simulação da norma L1 do associador
    associator_norm_l1 = np.sum(np.abs(u_sparse * v_sparse * p_sparse)) * 0.01

    constraints = [
        "batched_kvs_lookup",
        "sparse_sampling_1_in_4",
        "l1_norm_instead_of_l2",
        "fano_symmetry_reduction"
    ]

    public_outputs = {
        'associator_norm': float(associator_norm_l1),
        'sparse_points_evaluated': len(sparse_indices)
    }

    private_witness = {
        'sum_components': float(np.sum(u_sparse) + np.sum(v_sparse))
    }

    from track1_gtzk_wrapper import GTZKInstruction
    instruction = GTZKInstruction(
        name='track3_associator_opt',
        public_inputs={'grid_size': grid_size, 'total_points': len(u)},
        private_witness=private_witness,
        constraints=constraints
    )

    return instruction, public_outputs
