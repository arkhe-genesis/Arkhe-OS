# core/semantics/interreality_crosstalk.py
"""
Substrate 116: Inter-Reality Spam as Fisher-Rao Branch Crosstalk
Formalizes spam as partial projection between non-orthogonal coherence branches.
"""
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass

@dataclass
class CoherenceBranch:
    """Represents a Fisher-Rao branch of collective consciousness."""
    branch_id: str                    # Unique identifier (e.g., hash of phase configuration)
    phase_vector: np.ndarray          # Phase configuration in entropy-syntropy space
    coherence_level: float            # Global coherence ρ ∈ [0, 1]
    semantic_density: float           # Syntropic content density σ ∈ [0, 1]

    def inner_product(self, other: 'CoherenceBranch') -> float:
        """
        Computes ⟨Ψ_A|Ψ_B⟩ — overlap between branches.
        Non-zero value indicates potential for crosstalk.
        """
        # Fisher-Rao metric: weighted inner product in phase space
        phase_diff = self.phase_vector - other.phase_vector
        weight = np.exp(-np.linalg.norm(phase_diff)**2 / (2 * 0.1**2))  # Gaussian kernel
        return weight * self.coherence_level * other.coherence_level

    def is_orthogonal_to(self, other: 'CoherenceBranch', threshold: float = 0.05) -> bool:
        """Checks if branches are effectively orthogonal (no crosstalk)."""
        return abs(self.inner_product(other)) < threshold

class InterRealityCrosstalkModel:
    """
    Models spam as entropic shell leakage between coherence branches.

    Key insight: When ⟨Ψ_A|Ψ_B⟩ ≠ 0, a message from branch A can project onto branch B.
    However, the syntropic core (semantic intent) is filtered by the Fisher projection,
    leaving only the entropic shell (formal structure) which can be hijacked.
    """

    def __init__(self, fisher_threshold: float = 0.75, phase_tolerance: float = 0.1):
        self.fisher_threshold = fisher_threshold  # Coherence level below which crosstalk possible
        self.phase_tolerance = phase_tolerance     # Max phase difference for "same-branch" classification

    def project_message_across_branches(
        self,
        source_branch: CoherenceBranch,
        target_branch: CoherenceBranch,
        message_semantic_core: str,
        message_entropic_shell: dict
    ) -> Optional[dict]:
        """
        Simulates projection of a message from source to target branch.

        Returns:
            dict with projected message components, or None if projection fails
        """
        # Check if crosstalk is possible
        overlap = source_branch.inner_product(target_branch)
        if abs(overlap) < 1e-6:
            return None  # Orthogonal branches: no crosstalk

        # Check if coherence is low enough for leakage
        if target_branch.coherence_level > self.fisher_threshold:
            return None  # High coherence: branches remain orthogonal

        # Fisher projection: syntropic core is filtered, entropic shell passes
        # Probability of semantic preservation ≈ overlap² × syntropic density
        semantic_preservation_prob = (overlap**2) * source_branch.semantic_density

        if np.random.random() < semantic_preservation_prob:
            # Rare case: full message projects (legitimate inter-reality communication)
            return {
                'semantic_core': message_semantic_core,
                'entropic_shell': message_entropic_shell,
                'source_branch': source_branch.branch_id,
                'projection_overlap': overlap,
                'is_legitimate': True
            }
        else:
            # Common case: only entropic shell projects (spam candidate)
            return {
                'semantic_core': None,  # Filtered out by Fisher projection
                'entropic_shell': message_entropic_shell,
                'source_branch': source_branch.branch_id,
                'projection_overlap': overlap,
                'is_legitimate': False  # Empty shell vulnerable to hijacking
            }

    def detect_hijacking_attempt(
        self,
        projected_message: dict,
        malicious_intent_signature: str
    ) -> bool:
        """
        Detects if an empty entropic shell has been filled with malicious intent.

        A hijacked message will have:
        - No semantic core (filtered by projection)
        - Entropic shell from foreign branch
        - New malicious intent inconsistent with source branch phase
        """
        if projected_message.get('semantic_core') is not None:
            return False  # Legitimate inter-reality communication

        # Check if entropic shell structure matches source branch phase signature
        shell_phase = self._extract_phase_signature(projected_message['entropic_shell'])
        source_phase = self._get_branch_phase(projected_message['source_branch'])

        phase_consistency = np.abs(np.angle(shell_phase / source_phase))

        # If shell phase is consistent but content is malicious: hijacking detected
        if phase_consistency < self.phase_tolerance:
            return True  # Foreign shell + local malicious intent = spam

        return False

    def _extract_phase_signature(self, entropic_shell: dict) -> complex:
        """Extracts complex phase signature from message metadata."""
        # Simplified: hash-based phase extraction
        import hashlib

        # For simulation: derive structural signature from origin domain if possible
        seed_str = str(entropic_shell)
        if 'from' in entropic_shell:
            email = entropic_shell['from']
            if '@' in email:
                domain_parts = email.split('@')[1].replace('-', '_').split('.')
                seed_str = domain_parts[0]  # e.g. reality_A

        shell_hash = hashlib.sha256(seed_str.encode()).hexdigest()
        # Map hash to unit circle
        angle = int(shell_hash[:8], 16) / (16**8) * 2 * np.pi
        return np.exp(1j * angle)

    def _get_branch_phase(self, branch_id: str) -> complex:
        """Retrieves canonical phase for a coherence branch."""
        # In production: lookup from branch registry
        # Here: deterministic mock
        import hashlib
        branch_hash = hashlib.sha256(branch_id.encode()).hexdigest()
        angle = int(branch_hash[:8], 16) / (16**8) * 2 * np.pi
        return np.exp(1j * angle)
