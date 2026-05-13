#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qnc_transfer.py — Substrato 6178: Quantum Genomic Transfer Learning
Extende QNC com capacidade de transferência entre espécies.
"""

import numpy as np
from scipy.linalg import sqrtm
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from arkhe.layers.sigha_core import FisherBuresManifold, NaturalGradientFlow
from arkhe.layers.qnc_expanded import QuantumGenomicNetwork, GenomicEmbedding, PhiCGatedAttention


@dataclass
class SpeciesEmbedding:
    """Embedding que codifica a identidade da espécie no espaço quântico."""
    species_name: str
    embedding_rho: np.ndarray
    base_resistance: float
    genomic_signature: str


class MultiSpeciesQNC:
    """
    Rede neural quântica com transfer learning entre espécies.

    Arquitetura:
        Genomic Embedding → Shared Q-Conv → Φ_C-Attention → Species Adapter → Classifier
    """

    def __init__(self, max_len=128, hidden_dim=4):
        self.max_len = max_len
        self.hidden_dim = hidden_dim
        self.genomic_embedding = GenomicEmbedding(max_len)
        self.attention = PhiCGatedAttention(hidden_dim, hidden_dim, hidden_dim)
        self.species_adapters: Dict[str, np.ndarray] = {}
        self.classifier = [np.eye(hidden_dim, dtype=complex) / hidden_dim for _ in range(2)]
        self.manifold = FisherBuresManifold(hidden_dim)
        self.phi_c_field = np.eye(hidden_dim, dtype=complex) / hidden_dim
        self.trained_species: List[str] = []
        self.shared_knowledge: Dict[str, np.ndarray] = {}

    def register_species(self, name: str, base_resistance: float):
        """Registra nova espécie no modelo."""
        if name not in self.species_adapters:
            adapter = np.eye(self.hidden_dim, dtype=complex) / self.hidden_dim
            adapter += 0.01 * (np.random.randn(self.hidden_dim, self.hidden_dim) +
                              1j * np.random.randn(self.hidden_dim, self.hidden_dim))
            adapter = 0.5 * (adapter + adapter.conj().T)
            tr = np.trace(adapter).real
            if tr > 0:
                adapter /= tr
            self.species_adapters[name] = adapter

    def encode_species(self, sequence: str, species_name: str) -> np.ndarray:
        """Codifica sequência genômica com adaptação da espécie."""
        rho_seq = self.genomic_embedding.encode(sequence)
        query_rho = np.mean(rho_seq, axis=0)
        query_rho = 0.5 * (query_rho + query_rho.conj().T)
        # Add a tiny bit of identity to avoid singular matrices for sqrtm
        query_rho += 1e-6 * np.eye(self.hidden_dim, dtype=complex)
        tr = np.trace(query_rho).real
        if tr > 0:
            query_rho /= tr

        rho_seq_smoothed = []
        for r in rho_seq:
            r_new = r + 1e-6 * np.eye(self.hidden_dim, dtype=complex)
            r_new = 0.5 * (r_new + r_new.conj().T)
            r_new /= np.trace(r_new).real
            rho_seq_smoothed.append(r_new)
        rho_seq_smoothed = np.stack(rho_seq_smoothed)

        context = self.attention.forward(query_rho, rho_seq_smoothed, rho_seq_smoothed, self.phi_c_field)
        adapter = self.species_adapters.get(species_name, np.eye(self.hidden_dim, dtype=complex)/self.hidden_dim)
        adapted_context = adapter @ context @ adapter.conj().T
        tr = np.trace(adapted_context).real
        return adapted_context / tr if tr > 0 else adapted_context

    def forward(self, sequence: str, species_name: str = "unknown") -> np.ndarray:
        """Forward pass com adaptação de espécie."""
        adapted = self.encode_species(sequence, species_name)
        logits = []
        for w in self.classifier:
            logits.append(np.real(np.trace(adapted @ w)))
        return np.array(logits)

    def pretrain_on_all_species(self, species_data: Dict[str, List[Tuple[str, int]]],
                                 epochs: int = 50, lr: float = 0.03) -> List[float]:
        """Pré-treinamento multi-espécie."""
        loss_history = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            n_samples = 0
            for species_name, sequences in species_data.items():
                self.register_species(species_name, 5.0)
                for seq, label in sequences:
                    loss = self._train_step(seq, label, species_name, lr)
                    epoch_loss += loss
                    n_samples += 1
            loss_history.append(epoch_loss / max(1, n_samples))
            if epoch % 10 == 0:
                print(f"   Pretrain epoch {epoch:3d}: loss={loss_history[-1]:.6f}")
        self.trained_species = list(species_data.keys())
        return loss_history

    def finetune_species(self, species_name: str, sequences: List[Tuple[str, int]],
                          epochs: int = 20, lr: float = 0.01, freeze_shared: bool = True) -> List[float]:
        """Fine-tuning para espécie específica."""
        self.register_species(species_name, 5.0)
        loss_history = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for seq, label in sequences:
                loss = self._train_step(seq, label, species_name, lr, freeze_shared)
                epoch_loss += loss
            loss_history.append(epoch_loss / len(sequences))
        if species_name not in self.trained_species:
            self.trained_species.append(species_name)
        return loss_history

    def zero_shot_predict(self, sequence: str) -> Tuple[int, float]:
        """Predição zero-shot para espécie nunca vista."""
        adapted = self.encode_species(sequence, "unknown")
        logits = []
        for w in self.classifier:
            logits.append(np.real(np.trace(adapted @ w)))
        pred = 1 if logits[1] > logits[0] else 0
        confidence = abs(logits[1] - logits[0]) / (abs(logits[0]) + abs(logits[1]) + 1e-12)
        return pred, confidence

    def _train_step(self, sequence, label, species_name, lr, freeze_shared=False):
        """Passo de treinamento."""
        logits = self.forward(sequence, species_name)
        target = np.zeros_like(logits)
        target[label] = 1.0
        grad = logits - target

        adapted = self.encode_species(sequence, species_name)
        for i, w in enumerate(self.classifier):
            weight_grad = grad[i] * adapted
            self.classifier[i] = w - lr * weight_grad
            self.classifier[i] = 0.5 * (self.classifier[i] + self.classifier[i].conj().T)
            tr = np.trace(self.classifier[i]).real
            if tr > 0:
                self.classifier[i] /= tr

        if not freeze_shared:
            adapter = self.species_adapters.get(species_name)
            if adapter is not None:
                adapter_grad = sum(grad[i] * self.classifier[i] for i in range(2))
                adapter_new = adapter - lr * 0.5 * adapter_grad
                adapter_new = 0.5 * (adapter_new + adapter_new.conj().T)
                tr = np.trace(adapter_new).real
                if tr > 0:
                    adapter_new /= tr
                self.species_adapters[species_name] = adapter_new

        return np.sum(grad**2)

    def transfer_knowledge_to_species(self, source_species: str, target_species: str):
        """Transfere conhecimento de espécie fonte para alvo."""
        if source_species not in self.species_adapters:
            raise ValueError(f"Source species {source_species} not registered")
        source_adapter = self.species_adapters[source_species]
        base_adapter = np.eye(self.hidden_dim, dtype=complex) / self.hidden_dim
        # Interpolação quântica simplificada
        target_adapter = 0.3 * base_adapter + 0.7 * source_adapter
        target_adapter = 0.5 * (target_adapter + target_adapter.conj().T)
        tr = np.trace(target_adapter).real
        if tr > 0:
            target_adapter /= tr
        self.species_adapters[target_species] = target_adapter

    def compute_transfer_efficiency(self, source: str, target: str,
                                     target_data: List[Tuple[str, int]]) -> float:
        """Mede eficiência de transferência."""
        self.register_species(f"{target}_scratch", 5.0)
        loss_scratch = self.finetune_species(f"{target}_scratch", target_data, epochs=20, lr=0.01)

        self.transfer_knowledge_to_species(source, f"{target}_transfer")
        loss_transfer = self.finetune_species(f"{target}_transfer", target_data, epochs=20, lr=0.01)

        initial_loss_scratch = loss_scratch[0]
        initial_loss_transfer = loss_transfer[0]
        efficiency = (initial_loss_scratch - initial_loss_transfer) / (initial_loss_scratch + 1e-12)
        return max(0.0, efficiency)


def demo_transfer_learning():
    from arkp_bio.extremophile_analyzer import EXTREMOPHILE_DATABASE

    print("🌀 Quantum Genomic Transfer Learning — Demonstração")
    print("=" * 60)

    model = MultiSpeciesQNC(max_len=64, hidden_dim=4)

    # Preparar dados multi-espécie
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:20] + "ATCG"*10)[:64].ljust(64, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(5)]

    # Pré-treinamento
    print("\n📚 Pré-treinamento multi-espécie (5 organismos):")
    pretrain_loss = model.pretrain_on_all_species(species_data, epochs=30)

    # Transferência
    print("\n🔄 Teste de transferência:")
    print("   Deinococcus radiodurans (15 kGy) → Thermococcus gammatolerans (30 kGy)")

    target_seq = ("Thermococcus gamma" + "ATCG"*10)[:64].ljust(64, 'N')
    target_data = [(target_seq, 1) for _ in range(10)]

    eff = model.compute_transfer_efficiency(
        "Deinococcus radiodurans", "Thermococcus gammatolerans", target_data
    )
    print(f"   Eficiência de transferência: {eff*100:.1f}%")

    # Zero-shot
    print("\n🎯 Predição zero-shot para espécie desconhecida:")
    new_seq = "Pyrococcus furiosus"[:20].ljust(64, 'N') + "ATCG"*10
    pred, conf = model.zero_shot_predict(new_seq[:64])
    print(f"   Pyrococcus furiosus: pred={pred} (1=resistente), confiança={conf:.4f}")

    return model, eff


if __name__ == "__main__":
    demo_transfer_learning()
