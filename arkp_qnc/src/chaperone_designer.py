#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chaperone_designer.py — Substrato 6176: Design de Chaperonas via QNC
Usa a rede quântica treinada para prever e otimizar sequências de ligação
para chaperonas moleculares (Hsp70, GroEL).
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

from .genomic_qnc import GenomicQNC
from .quantum_layers import fidelity
from arkp_bio.chaperone_oracle_specific import SpecificChaperoneOracle, ChaperoneParams

@dataclass
class ChaperoneDesignResult:
    original_sequence: str
    suggested_mutations: List[Dict]
    predicted_affinity_before: float
    predicted_affinity_after: float
    confidence: float
    phi_c_contribution: float

class QNCChaperoneDesigner:
    """
    Designer de sequências de ligação para chaperonas usando QNC.

    Funcionalidades:
    • Predizer afinidade de ligação para proteína + chaperona
    • Sugerir mutações para aumentar afinidade
    • Otimizar sequência mantendo função original
    """

    CHAPERONE_TYPES = {
        'Hsp70': ChaperoneParams(
            name="Hsp70",
            binding_affinity=0.85,
            atp_hydrolysis_rate=12.5,
            conformational_change_energy=15.2,
            phi_c_coupling=0.12,
            cycle_time_ms=50.0,
        ),
        'GroEL': ChaperoneParams(
            name="GroEL",
            binding_affinity=0.92,
            atp_hydrolysis_rate=8.3,
            conformational_change_energy=22.1,
            phi_c_coupling=0.18,
            cycle_time_ms=120.0,
        ),
    }

    def __init__(self, qnc_model: GenomicQNC):
        self.model = qnc_model
        self.chaperone_oracles = {
            name: SpecificChaperoneOracle(
                phi_c_field=qnc_model.phi_c_field,
                chaperone_type=name
            )
            for name in self.CHAPERONE_TYPES
        }

    def predict_binding_affinity(
        self,
        protein_sequence: str,
        chaperone_type: str = 'GroEL'
    ) -> Dict:
        """
        Prediz afinidade de ligação entre proteína e chaperona.

        Returns:
            Dict com affinity_score, confidence, e contribuições
        """
        if chaperone_type not in self.CHAPERONE_TYPES:
            raise ValueError(f"Unknown chaperone type: {chaperone_type}")

        # Usar QNC para extrair representação quântica da proteína
        # (simplificado: usar logits como proxy para "binding potential")
        logits = self.model.forward(protein_sequence)

        # Score de afinidade: combinação de logits + coerência Φ_C
        phi_c_coherence = fidelity(
            self.model.phi_c_field,
            np.eye(self.model.config.hidden_dim) / self.model.config.hidden_dim
        )

        # Combinar: 70% QNC prediction, 30% Φ_C coherence
        affinity_score = 0.7 * np.exp(logits[1]) / (np.exp(logits[0]) + np.exp(logits[1]) + 1e-12)
        affinity_score += 0.3 * phi_c_coherence * self.CHAPERONE_TYPES[chaperone_type].phi_c_coupling

        return {
            'affinity_score': float(np.clip(affinity_score, 0.0, 1.0)),
            'qnc_contribution': float(logits[1] / (np.sum(np.exp(logits)) + 1e-12)),
            'phi_c_contribution': float(phi_c_coherence),
            'chaperone_coupling': self.CHAPERONE_TYPES[chaperone_type].phi_c_coupling,
            'confidence': float(np.max(np.exp(logits) / (np.sum(np.exp(logits)) + 1e-12))),
        }

    def suggest_mutations(
        self,
        protein_sequence: str,
        chaperone_type: str = 'GroEL',
        target_affinity: float = 0.8,
        max_mutations: int = 3
    ) -> ChaperoneDesignResult:
        """
        Sugere mutações para aumentar afinidade de ligação.
        """
        # Avaliar afinidade atual
        current_affinity = self.predict_binding_affinity(protein_sequence, chaperone_type)

        suggested_mutations = []
        best_sequence = protein_sequence
        best_affinity = current_affinity['affinity_score']

        # Heurística: posições "seguras" para mutação
        critical_residues = set(['W', 'F', 'Y', 'C', 'M'])

        for pos in range(len(protein_sequence)):
            if len(suggested_mutations) >= max_mutations:
                break

            original_aa = protein_sequence[pos]

            if original_aa in critical_residues:
                continue

            # Testar mutações conservativas
            for mutant_aa in ['A', 'S', 'T', 'V', 'L']:
                if mutant_aa == original_aa:
                    continue

                # Criar sequência mutante
                mutant_seq = protein_sequence[:pos] + mutant_aa + protein_sequence[pos+1:]

                # Avaliar afinidade
                mutant_affinity = self.predict_binding_affinity(mutant_seq, chaperone_type)

                if mutant_affinity['affinity_score'] > best_affinity:
                    best_affinity = mutant_affinity['affinity_score']
                    best_sequence = mutant_seq

                    suggested_mutations.append({
                        'position': pos,
                        'original': original_aa,
                        'mutant': mutant_aa,
                        'affinity_gain': mutant_affinity['affinity_score'] - current_affinity['affinity_score'],
                        'predicted_affinity': mutant_affinity['affinity_score'],
                    })
                    break  # Aceitar primeira melhoria e continuar

        return ChaperoneDesignResult(
            original_sequence=protein_sequence,
            suggested_mutations=suggested_mutations,
            predicted_affinity_before=current_affinity['affinity_score'],
            predicted_affinity_after=best_affinity,
            confidence=current_affinity['confidence'],
            phi_c_contribution=current_affinity['phi_c_contribution'],
        )

    def design_optimal_binding_sequence(
        self,
        protein_function: str,
        chaperone_type: str = 'GroEL',
        max_iterations: int = 10
    ) -> Dict:
        """
        Projetar sequência ótima para ligação a chaperona mantendo função.
        """
        initial_seq = self._function_to_seed_sequence(protein_function)

        best_seq = initial_seq
        best_score = -float('inf')

        for iteration in range(max_iterations):
            affinity = self.predict_binding_affinity(best_seq, chaperone_type)
            phi_c_coherence = fidelity(
                self.model.phi_c_field,
                np.eye(self.model.config.hidden_dim) / self.model.config.hidden_dim
            )

            score = (0.5 * affinity['affinity_score'] +
                    0.3 * phi_c_coherence +
                    0.2 * self._sequence_stability_score(best_seq))

            if score > best_score:
                best_score = score
            else:
                break

            best_seq = self._mutate_toward_higher_affinity(best_seq, chaperone_type)

        return {
            'final_sequence': best_seq,
            'final_affinity': self.predict_binding_affinity(best_seq, chaperone_type)['affinity_score'],
            'final_phi_c_coherence': phi_c_coherence,
            'iterations': iteration + 1,
            'improvement': best_score - (-float('inf')),
        }

    def _function_to_seed_sequence(self, function: str) -> str:
        patterns = {
            'DNA repair': 'MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGE',
            'chaperone binding': 'NLYIQWLKDGGPSSGRPPPSACDEFGHIKLMNPQRSTVWY',
            'folding assistant': 'ACDEFGHIKLMNPQRSTVWYMKWVTFISLLFLFSSAYSRG',
            'coherence sensor': 'GVFRRDTHKSEIAHRFKDLGENLYIQWLKDGGPSSGRPPP',
        }
        return patterns.get(function, 'ACDEFGHIKLMNPQRSTVWY' * 2)

    def _sequence_stability_score(self, sequence: str) -> float:
        hydrophobic = set(['A', 'V', 'L', 'I', 'M', 'F', 'W', 'Y'])
        consecutive = 0
        max_consecutive = 0

        for aa in sequence:
            if aa in hydrophobic:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0

        return max(0.0, 1.0 - max_consecutive / 10.0)

    def _mutate_toward_higher_affinity(self, sequence: str, chaperone_type: str) -> str:
        mutations = []

        for pos in range(len(sequence)):
            original = sequence[pos]
            mutant = sequence[:pos] + 'A' + sequence[pos+1:]

            affinity_orig = self.predict_binding_affinity(sequence, chaperone_type)['affinity_score']
            affinity_mut = self.predict_binding_affinity(mutant, chaperone_type)['affinity_score']

            if affinity_mut > affinity_orig:
                mutations.append((pos, 'A', affinity_mut - affinity_orig))

        if mutations:
            best_mut = max(mutations, key=lambda x: x[2])
            pos, aa, _ = best_mut
            return sequence[:pos] + aa + sequence[pos+1:]

        return sequence
