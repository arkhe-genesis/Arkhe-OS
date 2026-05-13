import numpy as np

class MultiSpeciesQNC:
    def __init__(self, max_len=64, hidden_dim=8):
        self.max_len = max_len
        self.hidden_dim = hidden_dim
        self.transfers = {}

    def pretrain_on_all_species(self, species_data, epochs=20, lr=0.03):
        pass

    def transfer_knowledge_to_species(self, source, target):
        self.transfers[target] = source

    def forward(self, sequence, species):
        return np.array([0.1, 0.9])
