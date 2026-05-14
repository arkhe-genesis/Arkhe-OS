#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
epigenetic_operators.py — Substrato 6180: Operadores Quânticos Epigenéticos
Modela modificações epigenéticas como operadores quânticos atuando no estado gênico.

Operadores implementados:
• MethylationOperator: Metilação de DNA (5mC) como operador de projeção
• HistoneModificationField: Campo quântico para acetilação, metilação de histonas
• ChromatinRemodelingOperator: Operador de remodelação de cromatina
• EpigeneticMemoryOperator: Operador de memória epigenética transgeracional
"""

import numpy as np
from scipy.linalg import sqrtm, expm, logm
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union
from enum import Enum, auto

# ============================================================================
# TIPOS DE MODIFICAÇÕES EPIGENÉTICAS
# ============================================================================

class EpigeneticMark(Enum):
    # Metilação de DNA
    DNA_5mC = auto()      # 5-metilcitosina (repressão)
    DNA_5hmC = auto()     # 5-hidroximetilcitosina (ativação intermediária)

    # Modificações de histonas
    H3K4me3 = auto()      # H3 lisina 4 tri-metilada (ativação promotora)
    H3K27ac = auto()      # H3 lisina 27 acetilada (ativação enhancer)
    H3K27me3 = auto()     # H3 lisina 27 tri-metilada (repressão Polycomb)
    H3K9me3 = auto()      # H3 lisina 9 tri-metilada (heterocromatina)
    H3K36me3 = auto()     # H3 lisina 36 tri-metilada (corpo do gene ativo)

    # Remodelação de cromatina
    OPEN_CHROMATIN = auto()  # Cromatina aberta (acessível)
    CLOSED_CHROMATIN = auto()  # Cromatina fechada (inacessível)

    # Não modificada
    UNMODIFIED = auto()

@dataclass
class EpigeneticState:
    """Estado epigenético de uma região genômica."""
    position: int  # Posição no genoma
    mark: EpigeneticMark
    confidence: float  # Confiança na chamada (0-1)
    quantum_amplitude: complex  # Amplitude quântica do estado
    heritability: float  # Potencial de herança transgeracional (0-1)
    temporal_stability: float  # Estabilidade temporal (0-1)

# ============================================================================
# OPERADOR DE METILAÇÃO QUÂNTICA
# ============================================================================

class MethylationOperator:
    """
    Operador quântico para metilação de DNA.

    A metilação é modelada como um operador de projeção que modifica
    a amplitude de expressão gênica no espaço de Hilbert epigenético.

    Equação: |ψ_methylated⟩ = M_θ |ψ_unmethylated⟩
    onde M_θ = cos(θ)I + i·sin(θ)·σ_z (rotação no espaço de expressão)
    """

    def __init__(self, methylation_strength: float = 0.5, context: str = 'promoter'):
        """
        Args:
            methylation_strength: Força da metilação (0 = nenhuma, 1 = completa)
            context: Contexto genômico ('promoter', 'gene_body', 'enhancer')
        """
        self.strength = np.clip(methylation_strength, 0.0, 1.0)
        self.context = context
        # Ângulo de rotação baseado na força e contexto
        self.theta = self._compute_rotation_angle()

    def _compute_rotation_angle(self) -> float:
        """Computa ângulo de rotação baseado em força e contexto."""
        base_angle = self.strength * np.pi / 2  # Máx: π/4 (45°)
        context_factors = {
            'promoter': 1.5,    # Metilação em promotor tem maior impacto
            'gene_body': 0.8,   # Metilação no corpo do gene tem impacto moderado
            'enhancer': 1.2,    # Metilação em enhancer tem impacto significativo
        }
        return base_angle * context_factors.get(self.context, 1.0)

    def apply(self, gene_state: np.ndarray) -> np.ndarray:
        """
        Aplica operador de metilação ao estado quântico do gene.

        Args:
            gene_state: Operador densidade representando estado de expressão

        Returns:
            Operador densidade após metilação
        """
        # Operador de rotação em torno do eixo Z
        # M_θ = exp(-i·θ·σ_z/2) = cos(θ/2)I - i·sin(θ/2)σ_z
        cos_term = np.cos(self.theta / 2)
        sin_term = np.sin(self.theta / 2)

        # Matriz de Pauli Z (para espaço de expressão binária: ativo/inativo)
        sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)

        # Operador de metilação
        M_theta = cos_term * np.eye(2) - 1j * sin_term * sigma_x

        # Operador de metilação


        # Aplicar ao estado (simplificado: ação por conjugação)
        if gene_state.shape == (2, 2):
            return M_theta @ gene_state @ M_theta.conj().T
        else:
            # Para estados de dimensão maior, aplicar em subespaço relevante
            dim = gene_state.shape[0]
            M_theta_expanded = np.eye(dim, dtype=complex)
            M_theta_expanded[:2, :2] = M_theta
            return M_theta_expanded @ gene_state @ M_theta_expanded.conj().T

    def repression_probability(self, gene_state: np.ndarray) -> float:
        """
        Calcula probabilidade de repressão gênica devido à metilação.

        Returns:
            Probabilidade de estado reprimido (0-1)
        """
        # Projetar no autoestado reprimido de σ_z
        if gene_state.shape == (2, 2):
            # Autoestado reprimido: |1⟩⟨1|
            repressed_proj = np.array([[0, 0], [0, 1]], dtype=complex)
            prob = np.real(np.trace(repressed_proj @ gene_state))
            return np.clip(prob, 0.0, 1.0)
        return 0.5  # Placeholder para dimensões maiores

# ============================================================================
# CAMPO QUÂNTICO DE MODIFICAÇÕES DE HISTONAS
# ============================================================================

class HistoneModificationField:
    """
    Campo quântico para modificações de histonas.

    Modela múltiplas modificações como um campo quântico que interfere
    construtiva ou destrutivamente na acessibilidade da cromatina.

    Equação: Φ_histone = Σᵢ αᵢ · |markᵢ⟩⟨markᵢ| + β · Σᵢⱼ γᵢⱼ · |markᵢ⟩⟨markⱼ|
    onde αᵢ são amplitudes individuais e γᵢⱼ são termos de interferência.
    """

    # Matriz de interferência entre marcas (empírica, baseada em literatura)
    INTERFERENCE_MATRIX = {
        (EpigeneticMark.H3K4me3, EpigeneticMark.H3K27ac): 0.8,   # Sinergia ativação
        (EpigeneticMark.H3K27me3, EpigeneticMark.H3K9me3): 0.7,  # Sinergia repressão
        (EpigeneticMark.H3K4me3, EpigeneticMark.H3K27me3): -0.9, # Antagonismo bivalente
        (EpigeneticMark.H3K36me3, EpigeneticMark.DNA_5mC): -0.6, # Antagonismo corpo do gene
    }

    def __init__(self, marks: List[EpigeneticState], coupling_strength: float = 0.1):
        """
        Args:
            marks: Lista de estados epigenéticos na região
            coupling_strength: Força de acoplamento entre marcas (Φ_C-like)
        """
        self.marks = marks
        self.coupling = coupling_strength
        self.field_operator = self._construct_field_operator()

    def _construct_field_operator(self) -> np.ndarray:
        """Constrói operador do campo de modificações de histonas."""
        dim = len(EpigeneticMark)
        field_op = np.zeros((dim, dim), dtype=complex)

        # Termos diagonais: amplitudes individuais
        for mark_state in self.marks:
            idx = list(EpigeneticMark).index(mark_state.mark)
            # Amplitude baseada em confiança e estabilidade temporal
            amplitude = mark_state.confidence * mark_state.temporal_stability
            field_op[idx, idx] = amplitude

        # Termos de interferência: acoplamento entre marcas
        for i, mark_i in enumerate(EpigeneticMark):
            for j, mark_j in enumerate(EpigeneticMark):
                if i != j:
                    key = (mark_i, mark_j)
                    if key in self.INTERFERENCE_MATRIX:
                        gamma = self.INTERFERENCE_MATRIX[key]
                        # Encontrar estados correspondentes
                        amp_i = next((m.confidence for m in self.marks if m.mark == mark_i), 0)
                        amp_j = next((m.confidence for m in self.marks if m.mark == mark_j), 0)
                        field_op[i, j] = self.coupling * gamma * amp_i * amp_j
                        field_op[j, i] = self.coupling * gamma * amp_i * amp_j

        return field_op

    def chromatin_accessibility(self) -> float:
        """
        Calcula acessibilidade da cromatina baseada no campo de histonas.

        Returns:
            Score de acessibilidade (0 = fechada, 1 = aberta)
        """
        # Autovalor dominante do campo (proxy para estado predominante)
        eigvals = np.linalg.eigvalsh(self.field_operator)
        dominant_eig = np.max(eigvals) if len(eigvals) > 0 else 0.0

        # Mapear para acessibilidade
        # Marcas de ativação contribuem positivamente, repressão negativamente
        activation_marks = {EpigeneticMark.H3K4me3, EpigeneticMark.H3K27ac, EpigeneticMark.H3K36me3}
        repression_marks = {EpigeneticMark.H3K27me3, EpigeneticMark.H3K9me3, EpigeneticMark.DNA_5mC}

        activation_score = sum(1 for m in self.marks if m.mark in activation_marks)
        repression_score = sum(1 for m in self.marks if m.mark in repression_marks)

        # Combinar com autovalor dominante
        accessibility = (
            0.4 * (activation_score / max(1, activation_score + repression_score)) +
            0.3 * (1 - repression_score / max(1, activation_score + repression_score)) +
            0.3 * (dominant_eig + 1) / 2  # Normalizar [-1,1] → [0,1]
        )

        return np.clip(accessibility, 0.0, 1.0)

    def predict_gene_expression(self, baseline_expression: float) -> float:
        """
        Prediz nível de expressão gênica considerando campo de histonas.

        Args:
            baseline_expression: Nível basal de expressão (sem modificações)

        Returns:
            Expressão predita (0-1)
        """
        accessibility = self.chromatin_accessibility()
        # Modelo simples: expressão = baseline × acessibilidade^exponent
        exponent = 1.5 if any(m.mark in {EpigeneticMark.H3K4me3, EpigeneticMark.H3K27ac}
                             for m in self.marks) else 1.0
        return min(1.0, baseline_expression * (1.0 + accessibility) ** exponent / (1.5**exponent))

# ============================================================================
# OPERADOR DE REMODELAÇÃO DE CROMATINA
# ============================================================================

class ChromatinRemodelingOperator:
    """
    Operador quântico para remodelação de cromatina.

    Modela a transição entre estados de cromatina aberta/fechada
    como uma evolução unitária no espaço de conformações.
    """

    def __init__(self, remodeling_energy: float = 1.0, atp_availability: float = 1.0):
        """
        Args:
            remodeling_energy: Energia disponível para remodelação (kcal/mol)
            atp_availability: Disponibilidade de ATP (0-1)
        """
        self.energy = remodeling_energy
        self.atp = atp_availability
        # Taxa de transição baseada em energia e ATP
        self.transition_rate = self.energy * self.atp * 0.1  # Heurística

    def evolve_chromatin_state(
        self,
        initial_state: np.ndarray,
        time_steps: int = 10,
    ) -> List[np.ndarray]:
        """
        Evolui estado de cromatina ao longo do tempo.

        Args:
            initial_state: Estado inicial de cromatina (operador densidade)
            time_steps: Número de passos de tempo

        Returns:
            Lista de estados ao longo do tempo
        """
        states = [initial_state]
        current = initial_state.copy()

        for t in range(time_steps):
            # Operador de evolução: U = exp(-i·H·Δt)
            # Hamiltoniano simplificado: H = -ΔE · σ_x (transição aberta↔fechada)
            delta_E = self.transition_rate
            dt = 0.1  # Passo de tempo
            H = -delta_E * np.array([[0, 1], [1, 0]], dtype=complex)  # σ_x

            # Exponencial do Hamiltoniano
            U = expm(-1j * H * dt)

            # Evoluir estado: ρ(t+Δt) = U · ρ(t) · U†
            current = U @ current @ U.conj().T

            # Projetar para operador densidade válido
            current = self._project_to_density_matrix(current)
            states.append(current)

        return states

    def _project_to_density_matrix(self, rho: np.ndarray) -> np.ndarray:
        """Projeta matriz para operador densidade válido."""
        # Hermitianizar
        rho = (rho + rho.conj().T) / 2
        # Projeção para positivo-semidefinido
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 0)
        # Normalizar traço
        trace = np.sum(eigvals)
        if trace > 1e-10:
            eigvals /= trace
        return eigvecs @ np.diag(eigvals) @ eigvecs.conj().T

# ============================================================================
# OPERADOR DE MEMÓRIA EPIGENÉTICA TRANSGERACIONAL
# ============================================================================

class EpigeneticMemoryOperator:
    """
    Operador quântico para memória epigenética transgeracional.

    Modela a herança de marcas epigenéticas através de divisões celulares
    e gerações como um processo quântico com decoerência controlada.
    """

    def __init__(self, heritability_factor: float = 0.8, decoherence_rate: float = 0.05):
        """
        Args:
            heritability_factor: Fator de herança (0 = nenhuma, 1 = perfeita)
            decoherence_rate: Taxa de decoerência por geração (0-1)
        """
        self.heritability = np.clip(heritability_factor, 0.0, 1.0)
        self.decoherence = np.clip(decoherence_rate, 0.0, 1.0)

    def transmit_across_generation(
        self,
        parent_epigenome: Dict[int, EpigeneticState],
        generation: int,
    ) -> Dict[int, EpigeneticState]:
        """
        Transmite epigenoma através de uma geração.

        Args:
            parent_epigenome: Dicionário {posição: estado epigenético} dos pais
            generation: Número da geração atual

        Returns:
            Epigenoma da geração atual com decoerência aplicada
        """
        child_epigenome = {}

        for pos, parent_state in parent_epigenome.items():
            # Probabilidade de herança com decoerência
            inheritance_prob = self.heritability * (1 - self.decoherence) ** generation

            if np.random.random() < inheritance_prob:
                # Herdar estado com possível mutação epigenética
                child_state = EpigeneticState(
                    position=pos,
                    mark=parent_state.mark,
                    confidence=parent_state.confidence * 0.95,  # Pequena perda de confiança
                    quantum_amplitude=parent_state.quantum_amplitude * np.exp(-1j * 0.01 * generation),
                    heritability=parent_state.heritability * 0.98,
                    temporal_stability=parent_state.temporal_stability * 0.99,
                )
                child_epigenome[pos] = child_state
            else:
                # Estado resetado para não-modificado
                child_epigenome[pos] = EpigeneticState(
                    position=pos,
                    mark=EpigeneticMark.UNMODIFIED,
                    confidence=0.5,
                    quantum_amplitude=1.0,
                    heritability=0.0,
                    temporal_stability=0.5,
                )

        return child_epigenome

    def compute_epigenetic_entropy(self, epigenome: Dict[int, EpigeneticState]) -> float:
        """
        Calcula entropia epigenética (diversidade de marcas).

        Returns:
            Entropia de Shannon das marcas epigenéticas
        """
        if not epigenome:
            return 0.0

        # Contar frequências de marcas
        mark_counts = {}
        for state in epigenome.values():
            mark = state.mark
            mark_counts[mark] = mark_counts.get(mark, 0) + 1

        # Calcular entropia
        total = len(epigenome)
        entropy = 0.0
        for count in mark_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)

        # Normalizar para [0,1]
        max_entropy = np.log2(len(EpigeneticMark))
        return entropy / max_entropy if max_entropy > 0 else 0.0
