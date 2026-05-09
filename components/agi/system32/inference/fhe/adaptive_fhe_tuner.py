#!/usr/bin/env python3
"""
adaptive_fhe_tuner.py — Dynamic FHE Parameter Tuner
Adjusts CKKS/TFHE parameters in real-time based on computational load and security requirements.
"""
import numpy as np
from typing import Dict, Tuple, Optional
import time

class AdaptiveFHETuner:
    def __init__(self, initial_params: Dict, min_security: int = 128, max_latency_ms: float = 100.0):
        self.params = initial_params  # {'ring_dim': 4096, 'modulus_bits': 40, 'noise_std': 3.2}
        self.min_security = min_security
        self.max_latency_ms = max_latency_ms
        self.history = []

    def update_parameters(self, current_load: float, security_requirement: int,
                          current_latency_ms: float) -> Dict:
        """Dynamically adjust FHE parameters based on runtime conditions."""
        # Monitor current state
        self.history.append({
            "time": time.time(),
            "load": current_load,
            "security_req": security_requirement,
            "latency": current_latency_ms,
            "params": self.params.copy()
        })

        # Optimization objective: minimize latency while maintaining security
        # Simplified gradient-based adjustment
        new_params = self.params.copy()

        # Adjust ring dimension based on load/latency trade-off
        if current_latency_ms > self.max_latency_ms:
            new_params['ring_dim'] = max(1024, self.params['ring_dim'] // 2)
        elif current_load < 0.6 and self.params['ring_dim'] < 16384:
            new_params['ring_dim'] = min(16384, self.params['ring_dim'] * 2)

        # Adjust modulus bits based on security requirements
        if security_requirement > self.min_security:
            new_params['modulus_bits'] = min(100, self.params['modulus_bits'] + 4)
        else:
            new_params['modulus_bits'] = max(32, self.params['modulus_bits'] - 2)

        # Adjust noise budget margin
        if current_load > 0.8:
            new_params['noise_std'] = min(4.5, self.params['noise_std'] + 0.1)
        else:
            new_params['noise_std'] = max(2.0, self.params['noise_std'] - 0.05)

        self.params = new_params
        return self.params

    def estimate_security_level(self, ring_dim: int, modulus_bits: int, noise_std: float) -> int:
        """Estimate security level in bits (simplified LWE/RLWE security estimator)."""
        # Simplified formula: Security ≈ 0.05 * ring_dim * log2(modulus_bits / noise_std)
        return int(0.05 * ring_dim * np.log2(max(1, modulus_bits / max(0.1, noise_std))))

    def verify_noise_budget(self, operations_count: int, depth: int) -> bool:
        """Check if current parameters have enough noise budget for planned operations."""
        noise_consumed = operations_count * 0.5 * (1 + 0.1 * depth)
        noise_budget = self.params['modulus_bits'] - (self.params['noise_std'] * 2)
        return noise_budget > noise_consumed + 2.0  # 2-bit safety margin
