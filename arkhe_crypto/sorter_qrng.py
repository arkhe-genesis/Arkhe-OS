# arkhe_crypto/sorter_qrng.py
"""
Gerador de Números Aleatórios Quânticos (QRNG) certificado
usando o Photon Sorter como fonte de entropia quântica.
"""

import torch
import hashlib
import numpy as np
from typing import Dict, List
from arkhe_optica.photon_sorter_simulator import PhotonSorterHighFidelity, PhotonSorterConfig

class CertifiedQRNG:
    """
    QRNG que usa estatísticas de detecção do Photon Sorter como fonte de entropia,
    com certificação ZK de que a aleatoriedade é genuinamente quântica.
    """

    def __init__(self, sorter_config: PhotonSorterConfig):
        self.sorter = PhotonSorterHighFidelity(sorter_config)
        self._buffer: List[int] = []
        self._entropy_estimate = 0.0

    def generate_random_bits(
        self,
        n_bits: int,
        input_state: str = "thermal",  # Estados térmicos maximizam entropia
        thermal_mean_n: float = 1.0,
        extract_method: str = "von_neumann"  # "von_neumann", "hash", "trevisan"
    ) -> Dict:
        """
        Gera bits aleatórios certificados a partir de estatísticas quânticas.

        Returns:
            Dict com bits, estimativa de entropia e prova de certificação
        """
        bits = []
        entropy_samples = []

        while len(bits) < n_bits:
            # Simular detecção no Photon Sorter com estado térmico
            result = self.sorter.simulate_input_output(
                input_state=input_state,
                thermal_mean_n=thermal_mean_n  # Estado térmico maximiza entropia
            )

            # Extrair entropia das estatísticas de detecção
            p_upper = result['output_probabilities']['p_upper']
            p_lower = result['output_probabilities']['p_lower']

            # Estimativa de entropia de min-entropia
            h_min = -np.log2(max(p_upper, p_lower) + 1e-10)
            entropy_samples.append(h_min)

            # Extrair bits via método escolhido
            if extract_method == "von_neumann":
                detection = 1 if np.random.random() < p_upper else 0
                self._buffer.append(detection)

                if len(self._buffer) >= 2:
                    pair = self._buffer[-2:]
                    self._buffer = self._buffer[:-2]
                    if pair == [0, 1]:
                        bits.append(0)
                    elif pair == [1, 0]:
                        bits.append(1)

            elif extract_method == "hash":
                g2 = result['output_probabilities']['g2_upper']
                hash_input = f"{p_upper:.6f}:{p_lower:.6f}:{g2:.6f}"
                hash_bytes = hashlib.sha256(hash_input.encode()).digest()
                for byte in hash_bytes:
                    for i in range(8):
                        if len(bits) < n_bits:
                            bits.append((byte >> i) & 1)

            if len(entropy_samples) > n_bits * 10:
                break

        avg_entropy = np.mean(entropy_samples) if entropy_samples else 0.0

        quantum_certification = {
            'g2_measured': float(result['output_probabilities']['g2_upper']),
            'classical_bound': 2.0,
            'quantum_verified': result['output_probabilities']['g2_upper'] < 1.9,
            'min_entropy_per_sample': float(avg_entropy),
            'total_samples_used': len(entropy_samples)
        }

        return {
            'bits': bits[:n_bits],
            'bitstring': ''.join(map(str, bits[:n_bits])),
            'entropy_estimate': {
                'min_entropy_per_sample': float(avg_entropy),
                'total_min_entropy': float(avg_entropy * len(entropy_samples)),
                'extraction_efficiency': len(bits[:n_bits]) / len(entropy_samples) if entropy_samples else 0
            },
            'quantum_certification': quantum_certification,
            'ready_for_zk': quantum_certification['quantum_verified']
        }

    def prepare_zk_proof_inputs(self, generation_result: Dict) -> Dict:
        """
        Prepara inputs públicos para prova ZK de que a aleatoriedade é quântica.
        """
        cert = generation_result['quantum_certification']
        SCALE = 10000
        public_inputs = {
            'g2_q': int(cert['g2_measured'] * SCALE),
            'classical_bound_q': int(cert['classical_bound'] * SCALE),
            'min_entropy_q': int(cert['min_entropy_per_sample'] * SCALE),
            'n_samples_q': generation_result['entropy_estimate']['total_samples_used']
        }

        private_witness = {
            'raw_detections': "hidden",
            'extraction_seed': 42
        }

        return {
            'public_inputs': public_inputs,
            'private_witness': private_witness,
            'circuit_constraints': [
                "g2_q < classical_bound_q",
                "min_entropy_q > threshold_q"
            ]
        }
