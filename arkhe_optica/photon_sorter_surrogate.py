# arkhe_optica/photon_sorter_surrogate.py
"""
Surrogate neural do Photon Sorter para otimização rápida no pipeline bidual.
Treinado com dataset gerado pelo simulador de alta fidelidade.
"""

import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple
import numpy as np

class PhotonSorterSurrogate(nn.Module):
    """
    Rede neural que aproxima a resposta do Photon Sorter de alta fidelidade.
    Input: parâmetros físicos + estado de entrada
    Output: probabilidades de detecção + métricas de qualidade
    """

    def __init__(self, hidden_dim: int = 128):
        super().__init__()

        # Encoding de parâmetros físicos (7 dimensões)
        self.param_encoder = nn.Sequential(
            nn.Linear(7, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim // 2)
        )

        # Encoding de estado de entrada (one-hot + amplitude)
        self.state_encoder = nn.Sequential(
            nn.Linear(5, hidden_dim),  # [coherent, fock1, fock2, thermal, amplitude]
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim // 2)
        )

        # Cabeça de predição
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 6)  # [p_upper, p_lower, n_total, g2_upper, g2_lower, sorting_fidelity]
        )

        # Softplus para garantir saídas positivas onde necessário
        self.softplus = nn.Softplus()

    def forward(self, physical_params: torch.Tensor, input_state: torch.Tensor) -> torch.Tensor:
        """
        physical_params: (batch, 7) = [omega_qd, gamma, gamma_d, beta, mzi_phase, mzi_imbalance, detector_eff]
        input_state: (batch, 5) = [is_coherent, is_fock1, is_fock2, is_thermal, amplitude]
        """
        # Codificar entradas
        param_emb = self.param_encoder(physical_params)
        state_emb = self.state_encoder(input_state)

        # Combinar e predizer
        combined = torch.cat([param_emb, state_emb], dim=1)
        raw_output = self.predictor(combined)

        # Aplicar ativações apropriadas
        output = torch.zeros_like(raw_output)
        output[:, 0:2] = torch.softmax(raw_output[:, 0:2], dim=1)  # p_upper, p_lower (probabilidades)
        output[:, 2] = self.softplus(raw_output[:, 2])  # n_total (positivo)
        output[:, 3:5] = torch.clamp(raw_output[:, 3:5], 0, 2)  # g² ∈ [0, 2]
        output[:, 5] = torch.sigmoid(raw_output[:, 5])  # sorting_fidelity ∈ [0, 1]

        return output

    def predict_sorting(self, beta: float, gamma_pure_mev: float,
                       detuning_mev: float, n_photons: int) -> Dict:
        """Interface de alta-level para predição de sorting (compatibilidade v1)"""
        # Mapear parâmetros simplificados para o formato do surrogate v2
        # physical_params: [omega_qd, gamma, gamma_d, beta, mzi_phase, mzi_imbalance, detector_eff]
        # input_state: [is_coherent, is_fock1, is_fock2, is_thermal, amplitude]

        physical_params = torch.tensor([[280.0, 1.0, gamma_pure_mev/10.0, beta, 0.0, 0.01, 0.95]])

        input_state = torch.zeros((1, 5))
        if n_photons == 1: input_state[0, 1] = 1.0
        elif n_photons == 2: input_state[0, 2] = 1.0
        else: input_state[0, 0] = 1.0; input_state[0, 4] = 0.1

        with torch.no_grad():
            pred = self.forward(physical_params, input_state).squeeze()

        return {
            'P_upper': float(pred[0]),
            'P_lower': float(pred[1]),
            'fidelity': float(pred[5]),
            'n_out': float(pred[2])
        }

    def generate_training_dataset(
        self,
        high_fidelity_sim,
        n_samples: int = 1000
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Gera dataset de treinamento amostrando espaço de parâmetros.
        """
        X_params = []
        X_states = []
        Y_targets = []

        state_types = ["coherent", "fock_1", "fock_2", "thermal"]

        for _ in range(n_samples):
            # Amostrar parâmetros físicos
            params = torch.tensor([
                np.random.uniform(270, 290),  # omega_qd_THz
                np.random.uniform(0.5, 2.0),   # gamma_GHz
                np.random.uniform(0.01, 0.5),  # gamma_d_GHz
                np.random.uniform(0.7, 1.0),   # beta
                np.random.uniform(0, 2*np.pi), # mzi_phase
                np.random.uniform(0, 0.05),    # mzi_imbalance
                np.random.uniform(0.8, 1.0)    # detector_eff
            ])

            # Amostrar estado de entrada
            state_type = np.random.choice(state_types)
            state_vec = torch.zeros(5)
            state_vec[state_types.index(state_type)] = 1.0
            state_vec[4] = np.random.uniform(0.01, 1.0) if state_type == "coherent" else 0.0

            # Simular com modelo de alta fidelidade
            result = high_fidelity_sim.simulate_input_output(
                input_state=state_type,
                input_amplitude=state_vec[4].item(),
                n_photons=1 if state_type == "fock_1" else 2 if state_type == "fock_2" else 0,
                thermal_mean_n=0.5 if state_type == "thermal" else 0.0
            )

            # Empacotar target
            target = torch.tensor([
                result['output_probabilities']['p_upper'],
                result['output_probabilities']['p_lower'],
                result['output_probabilities']['n_total'],
                result['output_probabilities']['g2_upper'],
                result['output_probabilities']['g2_lower'],
                result['sorting_fidelity']
            ])

            X_params.append(params)
            X_states.append(state_vec)
            Y_targets.append(target)

        return torch.stack(X_params), torch.stack(X_states), torch.stack(Y_targets)
