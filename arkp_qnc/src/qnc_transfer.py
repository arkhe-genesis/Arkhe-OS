import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from arkhe.layers.qnc_expanded import QuantumGenomicNetwork

class SpeciesEmbedding:
    pass

class MultiSpeciesQNC(QuantumGenomicNetwork):
    def __init__(self, max_len=128, hidden_dim=16, vocab_size=4, num_classes=2, phi_c_coupling=0.1):
        super().__init__(vocab_size, max_len, hidden_dim, num_classes)
        self.hidden_dim = hidden_dim
        self.trained_species = set()
        self.species_adapters = {}
        self.training_history = []

    def register_species(self, species_name, base_resistance=15.0):
        self.trained_species.add(species_name)
        # Initialize adapter as a density matrix
        adapter = np.eye(self.hidden_dim, dtype=complex) / self.hidden_dim
        self.species_adapters[species_name] = adapter

    def pretrain_on_all_species(self, species_data, epochs=20):
        losses = []
        for epoch in range(epochs):
            epoch_loss = 0
            count = 0
            for sp, data in species_data.items():
                if sp not in self.species_adapters:
                    self.register_species(sp)
                for seq, label in data:
                    loss = self.train_step(seq, label, lr=0.03)
                    epoch_loss += loss
                    count += 1
            losses.append(epoch_loss / max(1, count))

            # Record history
            self.training_history.append({"loss": epoch_loss / max(1, count)})
        return losses

    def encode_species(self, sequence, species_name):
        adapter = self.species_adapters.get(species_name, np.eye(self.hidden_dim, dtype=complex) / self.hidden_dim)
        # Simplified adaptation
        return adapter

    def zero_shot_predict(self, sequence):
        # returns class and confidence
        logits = self.forward(sequence)
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs)
        pred_class = int(np.argmax(probs))
        return pred_class, float(probs[pred_class])

    def predict(self, sequence):
        return self.zero_shot_predict(sequence)

    def transfer_knowledge_to_species(self, source_species, target_species):
        if source_species in self.species_adapters:
            # Transfer learning by copying adapter with slight mutation
            adapter = self.species_adapters[source_species].copy()
            noise = np.random.randn(*adapter.shape) * 0.01 + 1j * np.random.randn(*adapter.shape) * 0.01
            adapter += noise
            adapter = (adapter + adapter.conj().T) / 2
            adapter /= np.trace(adapter)
            self.species_adapters[target_species] = adapter
