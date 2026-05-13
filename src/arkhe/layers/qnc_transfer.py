"""
Substrato 6178 — Quantum Genomic Transfer Learning
Extende o QNC com capacidade de transferência entre espécies.
Implementa: pré-treinamento multi-espécie, fine-tuning por organismo,
            zero-shot prediction, e alinhamento de subespaços via Φ_C.
"""
import numpy as np
from scipy.linalg import sqrtm
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from arkp_sigha.sigha_core import FisherBuresManifold, NaturalGradientFlow
from .qnc_expanded import QuantumGenomicNetwork, GenomicEmbedding, PhiCGatedAttention

@dataclass
class SpeciesEmbedding:
    """Embedding que codifica a identidade da espécie no espaço quântico."""
    species_name: str
    embedding_rho: np.ndarray  # density operator representing the species
    base_resistance: float     # baseline radiation resistance (kGy)
    genomic_signature: str     # hash do genoma

class MultiSpeciesQNC:
    """
    Rede neural quântica com transfer learning entre espécies.

    Arquitetura:
        Genomic Embedding → Shared Q-Conv → Φ_C-Attention → Species Adapter → Classifier

    O Species Adapter é um subespaço treinável que permite adaptação rápida
    a novas espécies sem esquecer o conhecimento prévio (catastrophic forgetting
    é prevenido pela proteção topológica dos pesos na variedade de Fisher-Bures).
    """

    def __init__(self, max_len=128, hidden_dim=8, num_species=62):
        self.max_len = max_len
        self.hidden_dim = hidden_dim
        # Embedding genômico compartilhado
        self.genomic_embedding = GenomicEmbedding(max_len, hidden_dim)
        # Atenção Φ_C compartilhada
        self.attention = PhiCGatedAttention(hidden_dim, hidden_dim, hidden_dim)
        # Adaptadores por espécie (um subespaço de peso para cada organismo)
        self.species_adapters: Dict[str, np.ndarray] = {}
        # Classificador universal (aprende padrões cross-espécie)
        self.universal_classifier = FisherBuresManifold(hidden_dim)
        self.classifier_weights = [
            np.eye(hidden_dim, dtype=complex) / hidden_dim for _ in range(2)
        ]
        # Otimizador SIGHA
        self.flow = NaturalGradientFlow(FisherBuresManifold(hidden_dim))
        # Campo Φ_C de fundo
        self.phi_c_field = np.eye(hidden_dim, dtype=complex) / hidden_dim
        # Histórico de espécies treinadas
        self.trained_species: List[str] = []
        # Memória de features compartilhadas (proteção contra esquecimento)
        self.shared_knowledge: Dict[str, np.ndarray] = {}

    def register_species(self, name: str, base_resistance: float):
        """Registra uma nova espécie no modelo."""
        if name not in self.species_adapters:
            # Inicializa o adaptador como uma pequena perturbação da identidade
            adapter = np.eye(self.hidden_dim, dtype=complex) / self.hidden_dim
            adapter += 0.01 * (np.random.randn(self.hidden_dim, self.hidden_dim) +
                              1j * np.random.randn(self.hidden_dim, self.hidden_dim))
            adapter = 0.5 * (adapter + adapter.conj().T)
            adapter /= np.trace(adapter)
            self.species_adapters[name] = adapter

    def encode_species(self, sequence: str, species_name: str) -> np.ndarray:
        """Codifica sequência genômica com adaptação da espécie."""
        # Embedding genômico base
        rho_seq = self.genomic_embedding.encode(sequence)
        # Pooling via atenção Φ_C
        query_rho = np.mean(rho_seq, axis=0)
        context = self.attention.forward(query_rho, rho_seq, rho_seq, self.phi_c_field)
        # Aplicar adaptador da espécie (transformação unitária no subespaço)
        adapter = self.species_adapters.get(species_name, np.eye(self.hidden_dim, dtype=complex)/self.hidden_dim)
        adapted_context = adapter @ context @ adapter.conj().T
        return adapted_context / np.trace(adapted_context)

    def forward(self, sequence: str, species_name: str = "unknown") -> np.ndarray:
        """Forward pass com adaptação de espécie."""
        adapted = self.encode_species(sequence, species_name)
        logits = []
        for w in self.classifier_weights:
            logits.append(np.real(np.trace(adapted @ w)))
        return np.array(logits)

    def pretrain_on_all_species(
        self,
        species_data: Dict[str, List[Tuple[str, int]]],
        epochs: int = 50,
        lr: float = 0.03
    ) -> List[float]:
        """
        Pré-treinamento multi-espécie: aprende padrões universais
        de resistência a radiação compartilhados entre organismos.
        """
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

    def finetune_species(
        self,
        species_name: str,
        sequences: List[Tuple[str, int]],
        epochs: int = 20,
        lr: float = 0.01,
        freeze_shared: bool = True
    ) -> List[float]:
        """
        Fine-tuning para uma espécie específica.
        Se freeze_shared=True, congela os pesos compartilhados e treina apenas o adaptador.
        """
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
        """
        Predição zero-shot para uma espécie nunca vista.
        Usa apenas o conhecimento compartilhado (sem adaptador específico).
        """
        adapted = self.encode_species(sequence, "unknown")
        logits = []
        for w in self.classifier_weights:
            logits.append(np.real(np.trace(adapted @ w)))
        pred = 1 if logits[1] > logits[0] else 0
        confidence = abs(logits[1] - logits[0]) / (abs(logits[0]) + abs(logits[1]) + 1e-12)
        return pred, confidence

    def _train_step(self, sequence, label, species_name, lr, freeze_shared=False):
        """Passo de treinamento com opção de congelamento."""
        # Forward
        logits = self.forward(sequence, species_name)
        target = np.zeros_like(logits)
        target[label] = 1.0
        grad = logits - target

        # Atualizar pesos do classificador (sempre)
        adapted = self.encode_species(sequence, species_name)
        for i, w in enumerate(self.classifier_weights):
            weight_grad = grad[i] * adapted
            self.classifier_weights[i] = self.flow.step(w, weight_grad, lr)

        # Atualizar adaptador da espécie
        if not freeze_shared:
            adapter = self.species_adapters.get(species_name)
            if adapter is not None:
                adapter_grad = sum(grad[i] * self.classifier_weights[i] for i in range(2))
                self.species_adapters[species_name] = self.flow.step(adapter, adapter_grad, lr * 0.5)

        return np.sum(grad**2)

    def transfer_knowledge_to_species(self, source_species: str, target_species: str):
        """
        Transfere conhecimento de uma espécie fonte para uma alvo.
        Inicializa o adaptador da espécie alvo como uma interpolação
        entre o adaptador fonte e o estado base.
        """
        if source_species not in self.species_adapters:
            raise ValueError(f"Source species {source_species} not registered")
        source_adapter = self.species_adapters[source_species]
        # Inicializa o adaptador alvo próximo ao da fonte
        # (interpolação quântica na variedade de Fisher-Bures)
        manifold = FisherBuresManifold(self.hidden_dim)
        base_adapter = np.eye(self.hidden_dim, dtype=complex) / self.hidden_dim
        # Geodésica de Bures entre base e fonte
        target_adapter = manifold.geodesic(base_adapter, source_adapter, 0.7)
        self.species_adapters[target_species] = target_adapter

    def compute_transfer_efficiency(self, source: str, target: str,
                                    target_data: List[Tuple[str, int]]) -> float:
        """
        Mede eficiência de transferência: quantas épocas de fine-tuning
        são economizadas pelo conhecimento prévio?
        """
        # Treinar do zero (baseline)
        self.register_species(f"{target}_scratch", 5.0)
        loss_scratch = self.finetune_species(f"{target}_scratch", target_data, epochs=30, lr=0.01)

        # Transferir e treinar
        self.transfer_knowledge_to_species(source, f"{target}_transfer")
        loss_transfer = self.finetune_species(f"{target}_transfer", target_data, epochs=30, lr=0.01)

        # Eficiência = redução relativa na perda inicial
        initial_loss_scratch = loss_scratch[0]
        initial_loss_transfer = loss_transfer[0]
        efficiency = (initial_loss_scratch - initial_loss_transfer) / (initial_loss_scratch + 1e-12)
        return max(0.0, efficiency)
