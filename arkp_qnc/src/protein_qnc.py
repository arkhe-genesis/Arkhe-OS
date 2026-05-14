#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
protein_qnc.py — Extensão do QNC para proteínas (20 aminoácidos)
Embedding quântico para sequências proteicas + predição de estrutura/função.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from scipy.linalg import sqrtm
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from arkp_qnc.genomic_qnc import GenomicEmbedding, PhiCAttention
from arkp_qnc.quantum_layers import QuantumDenseLayer, QuantumDenseConfig

@dataclass
class AminoAcidProperties:
    """Propriedades físico-químicas de aminoácidos para embedding."""
    hydrophobicity: float  # -1.0 (hidrofílico) a +1.0 (hidrofóbico)
    charge: float  # -1, 0, +1
    volume: float  # Volume relativo (0-1)
    flexibility: float  # 0 (rígido) a 1 (flexível)
    polarity: float  # 0 (apolar) a 1 (polar)

# Tabela de propriedades de aminoácidos (valores normalizados)
AMINO_ACID_PROPERTIES = {
    'A': AminoAcidProperties(0.6, 0, 0.3, 0.8, 0.2),  # Alanine
    'R': AminoAcidProperties(-0.8, 1, 0.9, 0.6, 0.9),  # Arginine
    'N': AminoAcidProperties(-0.4, 0, 0.5, 0.7, 0.8),  # Asparagine
    'D': AminoAcidProperties(-0.9, -1, 0.4, 0.7, 0.9),  # Aspartate
    'C': AminoAcidProperties(0.4, 0, 0.4, 0.5, 0.3),  # Cysteine
    'E': AminoAcidProperties(-0.7, -1, 0.6, 0.7, 0.9),  # Glutamate
    'Q': AminoAcidProperties(-0.3, 0, 0.6, 0.7, 0.7),  # Glutamine
    'G': AminoAcidProperties(0.0, 0, 0.1, 1.0, 0.1),  # Glycine
    'H': AminoAcidProperties(-0.2, 0, 0.6, 0.6, 0.6),  # Histidine
    'I': AminoAcidProperties(0.9, 0, 0.7, 0.5, 0.2),  # Isoleucine
    'L': AminoAcidProperties(0.9, 0, 0.7, 0.6, 0.2),  # Leucine
    'K': AminoAcidProperties(-0.7, 1, 0.7, 0.7, 0.9),  # Lysine
    'M': AminoAcidProperties(0.7, 0, 0.6, 0.6, 0.3),  # Methionine
    'F': AminoAcidProperties(0.8, 0, 0.7, 0.5, 0.2),  # Phenylalanine
    'P': AminoAcidProperties(0.3, 0, 0.4, 0.3, 0.4),  # Proline
    'S': AminoAcidProperties(-0.3, 0, 0.3, 0.8, 0.6),  # Serine
    'T': AminoAcidProperties(-0.1, 0, 0.4, 0.7, 0.5),  # Threonine
    'W': AminoAcidProperties(0.7, 0, 0.9, 0.5, 0.4),  # Tryptophan
    'Y': AminoAcidProperties(0.4, 0, 0.7, 0.6, 0.5),  # Tyrosine
    'V': AminoAcidProperties(0.8, 0, 0.5, 0.6, 0.2),  # Valine
}

class ProteinEmbedding:
    """
    Embedding quântico para sequências proteicas.

    Cada aminoácido → estado puro em espaço de Hilbert 5D (propriedades).
    Sequência completa → produto tensorial com encoding posicional.
    """

    def __init__(self, max_len: int = 256, embedding_dim: int = 16):
        self.max_len = max_len
        self.embedding_dim = embedding_dim
        # Encoding posicional como fatores de fase
        self.pos_phases = np.exp(2j * np.pi * np.arange(max_len)[:, None] / max_len)

    def encode_sequence(self, sequence: str) -> List[np.ndarray]:
        """
        Codifica sequência proteica em lista de operadores densidade.

        Retorna: List[np.ndarray] de shape (max_len, 5, 5)
        """
        rho_list = []

        for i, aa in enumerate(sequence[:self.max_len]):
            if aa not in AMINO_ACID_PROPERTIES:
                # Aminoácido desconhecido → estado maximally mixed
                psi = np.ones(5) / np.sqrt(5)
            else:
                props = AMINO_ACID_PROPERTIES[aa]
                # Mapear propriedades para vetor de estado puro (5D)
                psi = np.array([
                    (props.hydrophobicity + 1) / 2,  # [0,1]
                    (props.charge + 1) / 2,
                    props.volume,
                    props.flexibility,
                    props.polarity,
                ])
                psi /= np.linalg.norm(psi)  # Normalizar

            # Estado puro → operador densidade
            rho = np.outer(psi, psi.conj())

            # Aplicar encoding posicional (fase global)
            phase = self.pos_phases[i % self.max_len, 0]
            rho = rho * phase.real

            rho_list.append(rho)

        # Padding com estados maximally mixed
        while len(rho_list) < self.max_len:
            rho_list.append(np.eye(5) / 5)

        return rho_list

    def pool_to_single(self, rho_list: List[np.ndarray]) -> np.ndarray:
        """Pool de lista de operadores para representação única."""
        # Atenção ponderada (pode ser substituída por atenção Φ_C)
        weights = np.array([1.0 / (i + 1) for i in range(len(rho_list))])
        weights /= weights.sum()
        return sum(w * rho for w, rho in zip(weights, rho_list))

class ProteinQNC:
    """
    Rede Neural Quântica para análise de proteínas.

    Arquitetura:
      Protein Embedding → Φ_C‑Attention → Quantum Dense → Classifier
    """

    def __init__(self, config: Dict):
        self.max_len = config.get("max_len", 256)
        self.hidden_dim = config.get("hidden_dim", 16)
        self.num_classes = config.get("num_classes", 3)  # e.g., stable/misfolded/aggregated

        # Componentes
        self.embedding = ProteinEmbedding(self.max_len, self.hidden_dim)
        self.attention = PhiCAttention(
            query_dim=self.hidden_dim,
            key_dim=self.hidden_dim,
            value_dim=self.hidden_dim,
        )
        self.classifier = QuantumDenseLayer(
            QuantumDenseConfig(
                input_dim=self.hidden_dim,
                output_dim=self.num_classes,
            )
        )

        # Campo Φ_C
        self.phi_c_field = np.eye(self.hidden_dim, dtype=complex) / self.hidden_dim

        # Histórico de treinamento
        self.training_history: List[Dict] = []

    def forward(self, sequence: str) -> np.ndarray:
        """Forward pass para sequência proteica."""
        # 1. Embedding proteico
        rho_sequence = self.embedding.encode_sequence(sequence)

        # 2. Pooling via atenção Φ_C
        query_rho = self.embedding.pool_to_single(rho_sequence)
        context_rho = self.attention.forward(
            query_rho,
            rho_sequence,
            rho_sequence,
            self.phi_c_field,
        )

        # 3. Classificação
        logits_rho = self.classifier.forward(context_rho)
        logits = np.real(np.diag(logits_rho))

        return logits

    def predict_structure(self, sequence: str) -> Dict:
        """
        Prediz características estruturais da proteína.

        Retorna: Dict com predicted_class, confidence, stability_score, etc.
        """
        logits = self.forward(sequence)
        probs = np.exp(logits - np.max(logits))
        probs /= np.sum(probs) + 1e-12

        predicted_class = int(np.argmax(probs))
        confidence = float(np.max(probs))

        # Score de estabilidade (heurística baseada em hidrofobicidade)
        hydrophobic_count = sum(1 for aa in sequence if aa in ['A', 'V', 'L', 'I', 'M', 'F', 'W', 'Y'])
        stability_score = min(1.0, hydrophobic_count / len(sequence) * 1.5) if sequence else 0.5

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "stability_score": stability_score,
            "phi_c_coherence": float(np.real(np.trace(self.phi_c_field))),
        }

    def suggest_stabilizing_mutations(
        self,
        sequence: str,
        max_mutations: int = 3,
    ) -> List[Dict]:
        """Sugere mutações para aumentar estabilidade estrutural."""
        suggestions = []
        current_stability = self.predict_structure(sequence)["stability_score"]

        for pos in range(len(sequence)):
            if len(suggestions) >= max_mutations:
                break

            original_aa = sequence[pos]

            # Testar mutações para aminoácidos mais hidrofóbicos (geralmente estabilizantes)
            for mutant_aa in ['A', 'V', 'L', 'I', 'M']:
                if mutant_aa == original_aa:
                    continue

                mutant_seq = sequence[:pos] + mutant_aa + sequence[pos+1:]
                mutant_stability = self.predict_structure(mutant_seq)["stability_score"]

                if mutant_stability > current_stability:
                    suggestions.append({
                        "position": pos,
                        "original": original_aa,
                        "mutant": mutant_aa,
                        "stability_gain": mutant_stability - current_stability,
                        "predicted_stability": mutant_stability,
                    })
                    break  # Aceitar primeira melhoria

        return suggestions
