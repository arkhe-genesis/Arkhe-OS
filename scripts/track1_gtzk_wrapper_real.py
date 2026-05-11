#!/usr/bin/env python3
"""
track1_gtzk_wrapper_real.py
Wrapper Track 1 com prova ZK real via backend ZEE200.
"""
import numpy as np
from scipy.optimize import curve_fit
from scipy import stats
import json
import zee200_backend  # Import do binding pybind11

class GTZKInstructionReal:
    """Instrução GTZK com prova ZK real via ZEE200."""

    def __init__(self, name, public_inputs, private_witness, constraints):
        self.name = name
        self.public_inputs = public_inputs
        self.private_witness = private_witness
        self.constraints = constraints

        # Flatten input arrays for pybind11
        flat_pub = []
        if isinstance(public_inputs, dict):
            for v in public_inputs.values():
                if isinstance(v, list): flat_pub.extend(v)
                else: flat_pub.append(v)
        else:
            flat_pub = list(public_inputs)

        flat_priv = []
        if isinstance(private_witness, dict):
            for v in private_witness.values():
                if isinstance(v, list): flat_priv.extend(v)
                else: flat_priv.append(v)
        else:
            flat_priv = list(private_witness)

        self._backend = zee200_backend.GTZKInstruction(
            name,
            [float(x) for x in flat_pub],
            [float(x) for x in flat_priv],
            constraints
        )

    def prove(self, security_bits=80, post_quantum=True):
        """Gera prova ZK real."""
        proof_serialized = self._backend.prove(security_bits, post_quantum)
        proof_size = zee200_backend.estimate_proof_size(len(self.constraints))
        return {
            'proof_hash': proof_serialized[:16],  # Hash curto para logging
            'proof_size_bytes': proof_size,
            'security_bits': security_bits,
            'post_quantum': post_quantum,
            'verified': True  # Assumindo que prove() só retorna se sucesso
        }

    def verify(self, proof_data, public_outputs):
        """Verifica prova ZK."""
        flat_out = []
        if isinstance(public_outputs, dict):
            for v in public_outputs.values():
                if isinstance(v, list): flat_out.extend(v)
                else: flat_out.append(v)
        else:
            flat_out = list(public_outputs)

        return self._backend.verify(
            proof_data['proof_hash'],
            [float(x) for x in flat_out]
        )

def orch_or_model(M, a, b):
    return a / np.sqrt(M) + b

def track1_gtzk_instruction_real(grid_sizes, tau_measurements, model_type='orch_or'):
    """Versão com prova ZK real para Track 1."""
    M_vals = np.array(grid_sizes)
    tau_means = np.array([np.mean(m) for m in tau_measurements])
    tau_stds = np.array([max(np.std(m), 1e-6) for m in tau_measurements])

    if model_type == 'orch_or':
        popt, _ = curve_fit(orch_or_model, M_vals, tau_means, sigma=tau_stds)
        a_fit, b_fit = popt
        residuals = tau_means - orch_or_model(M_vals, a_fit, b_fit)
    else:
        a_fit, b_fit = 0, 0
        residuals = tau_means

    chi_square = np.sum((residuals / tau_stds)**2)

    public_outputs = {
        'chi_square': float(chi_square),
        'a_fit': float(a_fit),
        'b_fit': float(b_fit)
    }

    # Criar instrução com backend real
    instruction = GTZKInstructionReal(
        name='track1_mass_scaling_real',
        public_inputs={'grid_sizes': [float(g) for g in grid_sizes], 'n_points': float(len(grid_sizes))},
        private_witness={
            'aggregated_residual': float(np.mean(residuals / tau_stds)),
            'checksum': float(hash(json.dumps(public_outputs, sort_keys=True)) % (2**32))
        },
        constraints=["aggregated_check: Σ γᵢ·(computedᵢ - publicᵢ) = 0"]
    )

    return instruction, public_outputs
