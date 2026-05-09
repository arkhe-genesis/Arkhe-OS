import torch
import torch.nn as nn
import numpy as np

class CliffordBiocomputer(nn.Module):
    def __init__(self, input_dim=64, cell_dim=64, num_axons=4):
        super().__init__()
        self.metabolism = nn.Linear(input_dim, 1)
        self.axons = nn.ModuleList([nn.Linear(input_dim, cell_dim) for _ in range(num_axons)])
        self.bivector_dim = (cell_dim * (cell_dim - 1)) // 2
        self.cortical_memory = nn.Linear(cell_dim, self.bivector_dim)
        self.output_projection = nn.Linear(cell_dim, input_dim)

    def forward(self, x):
        energy = torch.sigmoid(self.metabolism(x))
        axon_outputs = [torch.tanh(axon(x)) for axon in self.axons]
        combined_vector = torch.stack(axon_outputs).mean(dim=0)
        bivector_state = torch.tanh(self.cortical_memory(combined_vector))
        hesitation = 1.0 - energy
        final_state = combined_vector * energy
        action = self.output_projection(final_state)
        return action, {'energy': energy, 'vector': combined_vector, 'bivector': bivector_state, 'hesitation': hesitation}
