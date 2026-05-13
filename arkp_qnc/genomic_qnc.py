import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from arkhe.layers.qnc_expanded import QuantumGenomicNetwork, GenomicEmbedding, PhiCGatedAttention as PhiCAttention

class GenomicQNCConfig:
    def __init__(self, vocab_size=4, max_sequence_length=128, embedding_dim=8, hidden_dim=16, num_classes=2, phi_c_coupling=0.1):
        self.vocab_size = vocab_size
        self.max_sequence_length = max_sequence_length
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.phi_c_coupling = phi_c_coupling

class GenomicQNC(QuantumGenomicNetwork):
    def __init__(self, config=None):
        if config is None:
            config = GenomicQNCConfig()
        super().__init__(config.vocab_size, config.max_sequence_length, config.hidden_dim, config.num_classes)
        self.config = config
        self.phi_c_field = np.eye(config.hidden_dim, dtype=complex) / config.hidden_dim

    def predict(self, sequence):
        logits = self.forward(sequence)
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs)
        pred_class = int(np.argmax(probs))
        return pred_class, float(probs[pred_class])
