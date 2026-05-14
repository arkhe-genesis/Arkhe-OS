#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rna_quantum_embedding.py — Substrato 6180: RNA Quantum Embedding
Embedding quântico para sequências de RNA com propriedades estruturais e funcionais.

Tipos suportados:
• mRNA: mensageiro, com códons e UTRs
• tRNA: transportador, com estrutura em trevo e anticódon
• rRNA: ribossomal, com domínios catalíticos
• ncRNA: não-codificante (miRNA, lncRNA, siRNA) com alvos regulatórios
"""

import numpy as np
from scipy.linalg import sqrtm
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union
from enum import Enum, auto

# ============================================================================
# TIPOS DE RNA E SUAS PROPRIEDADES QUÂNTICAS
# ============================================================================

class RNAType(Enum):
    mRNA = auto()      # Mensageiro
    tRNA = auto()      # Transportador
    rRNA = auto()      # Ribossomal
    miRNA = auto()     # MicroRNA regulatório
    lncRNA = auto()    # Long non-coding RNA
    siRNA = auto()     # Small interfering RNA
    snRNA = auto()     # Small nuclear RNA
    Unknown = auto()

@dataclass
class RNAProperties:
    """Propriedades físico-químicas e funcionais de nucleotídeos de RNA."""
    # Propriedades de base
    base: str  # A, U, G, C
    hydrogen_bonds: int  # 2 (A-U) ou 3 (G-C)
    stacking_energy: float  # Energia de empilhamento (-kcal/mol)
    flexibility: float  # 0 (rígido) a 1 (flexível)

    # Propriedades funcionais (dependem do contexto)
    is_modified: bool  # Base modificada (m6A, pseudouridina, etc.)
    modification_type: Optional[str]  # Tipo de modificação
    structural_role: str  # 'stem', 'loop', 'bulge', 'junction', 'unstructured'

    # Propriedades quânticas
    coherence_lifetime: float  # Tempo de coerência estimado (ps)
    entanglement_potential: float  # Potencial de emaranhamento (0-1)

# Tabela de propriedades de nucleotídeos de RNA
RNA_NUCLEOTIDE_PROPERTIES = {
    'A': RNAProperties('A', 2, -3.2, 0.7, False, None, 'unstructured', 0.8, 0.3),
    'U': RNAProperties('U', 2, -2.8, 0.8, False, None, 'unstructured', 0.9, 0.4),
    'G': RNAProperties('G', 3, -3.8, 0.5, False, None, 'unstructured', 0.6, 0.5),
    'C': RNAProperties('C', 3, -3.4, 0.6, False, None, 'unstructured', 0.7, 0.4),
    # Bases modificadas comuns
    'm6A': RNAProperties('A', 2, -3.0, 0.6, True, 'm6A', 'loop', 0.5, 0.6),
    'Ψ': RNAProperties('U', 2, -3.1, 0.7, True, 'pseudouridine', 'stem', 0.7, 0.7),
    'm5C': RNAProperties('C', 3, -3.6, 0.5, True, 'm5C', 'stem', 0.6, 0.6),
}

# Propriedades específicas por tipo de RNA
RNA_TYPE_PROPERTIES = {
    RNAType.mRNA: {
        'avg_length': 2000,
        'has_5UTR': True,
        'has_3UTR': True,
        'has_polyA': True,
        'codon_aware': True,
        'quantum_features': ['codon_coherence', 'UTR_regulation', 'polyA_stability']
    },
    RNAType.tRNA: {
        'avg_length': 76,
        'cloverleaf_structure': True,
        'anticodon_position': (34, 36),
        'quantum_features': ['anticodon_recognition', 'aminoacylation_coherence']
    },
    RNAType.rRNA: {
        'avg_length': 1500,
        'catalytic_domains': True,
        'quantum_features': ['peptidyl_transfer_coherence', 'ribosome_assembly']
    },
    RNAType.miRNA: {
        'avg_length': 22,
        'seed_region': (2, 8),
        'target_complementarity': 'partial',
        'quantum_features': ['seed_target_entanglement', 'RISC_loading']
    },
}

# ============================================================================
# EMBEDDING QUÂNTICO PARA RNA
# ============================================================================

class RNAEmbedding:
    """
    Embedding quântico para sequências de RNA.

    Cada nucleotídeo → estado puro em espaço de Hilbert 5D:
    [base_encoding, stacking, flexibility, modification, structural_role]

    Sequência completa → produto tensorial com encoding posicional e tipo de RNA.
    """

    def __init__(self, max_len: int = 512, embedding_dim: int = 32, rna_type: RNAType = RNAType.mRNA):
        self.max_len = max_len
        self.embedding_dim = embedding_dim
        self.rna_type = rna_type
        self.type_properties = RNA_TYPE_PROPERTIES.get(rna_type, {})

        # Encoding posicional como fatores de fase + tipo de RNA
        self.pos_phases = np.exp(2j * np.pi * np.arange(max_len)[:, None] / max_len)
        self.type_encoding = self._encode_rna_type(rna_type)

    def _encode_rna_type(self, rna_type: RNAType) -> np.ndarray:
        """Codifica o tipo de RNA como vetor quântico."""
        # Mapeamento one-hot quântico para tipos de RNA
        type_map = {
            RNAType.mRNA: [1, 0, 0, 0, 0, 0, 0, 0],
            RNAType.tRNA: [0, 1, 0, 0, 0, 0, 0, 0],
            RNAType.rRNA: [0, 0, 1, 0, 0, 0, 0, 0],
            RNAType.miRNA: [0, 0, 0, 1, 0, 0, 0, 0],
            RNAType.lncRNA: [0, 0, 0, 0, 1, 0, 0, 0],
            RNAType.siRNA: [0, 0, 0, 0, 0, 1, 0, 0],
            RNAType.snRNA: [0, 0, 0, 0, 0, 0, 1, 0],
            RNAType.Unknown: [0, 0, 0, 0, 0, 0, 0, 1],
        }
        encoding = np.array(type_map.get(rna_type, type_map[RNAType.Unknown]))
        # Normalizar para estado puro
        return encoding / np.linalg.norm(encoding)

    def encode_sequence(self, sequence: str, structure: Optional[str] = None) -> List[np.ndarray]:
        """
        Codifica sequência de RNA em lista de operadores densidade.

        Args:
            sequence: String de RNA (A, U, G, C, ou bases modificadas)
            structure: Notação de estrutura secundária em dot-bracket (opcional)

        Returns:
            List[np.ndarray] de shape (max_len, dim, dim) — operadores densidade
        """
        rho_list = []

        for i, nucleotide in enumerate(sequence[:self.max_len]):
            # Obter propriedades do nucleotídeo
            props = RNA_NUCLEOTIDE_PROPERTIES.get(
                nucleotide,
                RNA_NUCLEOTIDE_PROPERTIES.get(nucleotide[0], RNA_NUCLEOTIDE_PROPERTIES['A'])
            )

            # Determinar papel estrutural
            if structure and i < len(structure):
                struct_char = structure[i]
                if struct_char == '(' or struct_char == ')':
                    structural_role = 'stem'
                elif struct_char == '.':
                    structural_role = 'loop' if i > 0 and structure[i-1] in '().' else 'unstructured'
                else:
                    structural_role = 'bulge'
            else:
                structural_role = props.structural_role

            # Mapear propriedades para vetor de estado puro (5D)
            psi = np.array([
                self._base_encoding(props.base),  # [0,1] encoding da base
                (props.stacking_energy + 4.0) / 4.0,  # Normalizar [-4,0] → [0,1]
                props.flexibility,
                1.0 if props.is_modified else 0.0,
                self._structural_role_encoding(structural_role),
            ])
            psi /= np.linalg.norm(psi)  # Normalizar para estado puro

            # Estado puro → operador densidade
            rho = np.outer(psi, psi.conj())

            # Aplicar encoding posicional + tipo de RNA
            phase = self.pos_phases[i % self.max_len, 0]
            rho = rho * phase.real  # Fase global (simplificado)

            # Incorporar tipo de RNA via produto tensorial parcial
            if self.embedding_dim >= 8:
                # Expandir para incluir tipo de RNA
                type_expanded = np.kron(rho, np.outer(self.type_encoding, self.type_encoding.conj()))
                # Resize ou pad para atingir embedding_dim
                target_rho = np.zeros((self.embedding_dim, self.embedding_dim), dtype=complex)
                copy_dim = min(type_expanded.shape[0], self.embedding_dim)
                target_rho[:copy_dim, :copy_dim] = type_expanded[:copy_dim, :copy_dim]
                rho = target_rho
                if np.trace(rho) > 0:
                    rho /= np.trace(rho)
            else:
                target_rho = np.zeros((self.embedding_dim, self.embedding_dim), dtype=complex)
                copy_dim = min(rho.shape[0], self.embedding_dim)
                target_rho[:copy_dim, :copy_dim] = rho[:copy_dim, :copy_dim]
                rho = target_rho
                if np.trace(rho) > 0:
                    rho /= np.trace(rho)

            rho_list.append(rho)

        # Padding com estados maximally mixed
        while len(rho_list) < self.max_len:
            rho_list.append(np.eye(self.embedding_dim) / self.embedding_dim)

        return rho_list

    def _base_encoding(self, base: str) -> float:
        """Codifica base nucleotídica como valor escalar [0,1]."""
        encoding = {'A': 0.0, 'U': 0.33, 'G': 0.66, 'C': 1.0}
        return encoding.get(base, 0.5)

    def _structural_role_encoding(self, role: str) -> float:
        """Codifica papel estrutural como valor escalar [0,1]."""
        encoding = {
            'stem': 0.0,
            'loop': 0.25,
            'bulge': 0.5,
            'junction': 0.75,
            'unstructured': 1.0,
        }
        return encoding.get(role, 0.5)

    def pool_to_single(self, rho_list: List[np.ndarray], attention_weights: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Pool de lista de operadores para representação única.

        Args:
            rho_list: Lista de operadores densidade
            attention_weights: Pesos de atenção (opcional)

        Returns:
            np.ndarray: Operador densidade pooled
        """
        if attention_weights is not None:
            # Atenção ponderada
            weights = attention_weights / (np.sum(attention_weights) + 1e-12)
            return sum(w * rho for w, rho in zip(weights, rho_list))
        else:
            # Média simples com decaimento posicional
            weights = np.array([1.0 / (i + 1) for i in range(len(rho_list))])
            weights /= weights.sum()
            return sum(w * rho for w, rho in zip(weights, rho_list))

    def extract_codons(self, sequence: str) -> List[Tuple[str, int, np.ndarray]]:
        """
        Extrai códons de mRNA como operadores quânticos.

        Returns:
            List of (codon, position, quantum_embedding)
        """
        if self.rna_type != RNAType.mRNA:
            return []

        codons = []
        for i in range(0, len(sequence) - 2, 3):
            codon = sequence[i:i+3]
            if len(codon) == 3 and all(c in 'AUCG' for c in codon):
                # Embedding do códon como produto tensorial dos 3 nucleotídeos
                nucleotide_rhos = [self.encode_sequence(nuc)[0] for nuc in codon]
                # Produto tensorial simplificado (média ponderada)
                codon_rho = sum(rho / 3 for rho in nucleotide_rhos)
                codons.append((codon, i, codon_rho))

        return codons
