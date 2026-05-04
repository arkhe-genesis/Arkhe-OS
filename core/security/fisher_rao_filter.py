# core/security/fisher_rao_filter.py
"""
Fisher-Rao Filter — Substrate 116 Anti-Spam Mechanism
Uses ZEE200 circuit to verify causal consistency via Jones invariant.
"""
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib

@dataclass
class MessageSignature:
    """Cryptographic signature with topological metadata."""
    sender_hash: str           # Hash of sender's public coherence state
    content_hash: str          # Hash of message content
    jones_invariant: complex   # Topological invariant of sender's causal history
    branch_phase: complex      # Phase signature of originating Fisher-Rao branch
    timestamp: float           # Logical timestamp (not physical time)

    def verify_causal_consistency(self, other: 'MessageSignature') -> Tuple[bool, float]:
        """
        Verifies if two signatures share consistent causal history.

        Returns:
            (is_consistent, phase_difference)
        """
        # Jones invariant should be consistent for same causal branch
        jones_ratio = self.jones_invariant / other.jones_invariant
        phase_diff = np.angle(jones_ratio)

        # Consistent if phase difference is near zero (mod 2π)
        is_consistent = abs(phase_diff) < 0.1  # Tolerance for numerical noise
        return is_consistent, abs(phase_diff)

class FisherRaoFilter:
    """
    Topological anti-spam filter based on causal consistency verification.

    Core principle: Legitimate messages from our branch have Jones invariants
    consistent with our local coherence field. Inter-reality spam has phase
    mismatch between entropic shell and malicious content.
    """

    def __init__(
        self,
        local_branch_phase: complex,
        coherence_threshold: float = 0.75,
        phase_tolerance: float = 0.1,
        jones_verification: bool = True
    ):
        self.local_phase = local_branch_phase
        self.coherence_threshold = coherence_threshold
        self.phase_tolerance = phase_tolerance
        self.jones_verification = jones_verification

        # Cache for sender reputation (optional)
        self._sender_cache: Dict[str, MessageSignature] = {}

    def compute_jones_invariant(self, causal_history: str) -> complex:
        """
        Computes Jones polynomial evaluation for a causal history string.

        This is a simplified Markov trace for Fibonacci anyon representation.
        In production: use full Temperley-Lieb algebra evaluation.
        """
        # Hash causal history to integer
        history_hash = int(hashlib.sha256(causal_history.encode()).hexdigest()[:16], 16)

        # Map to Fibonacci anyon trace: φ^Q + φ^(-Q) where Q = history_hash mod 10
        phi = (np.sqrt(5) - 1) / 2  # Golden ratio conjugate ≈ 0.618
        Q = history_hash % 10
        return phi**Q + phi**(-Q)

    def extract_message_signature(
        self,
        sender_id: str,
        content: str,
        metadata: Dict
    ) -> MessageSignature:
        """
        Extracts topological signature from message components.

        The signature encodes:
        - Sender's coherence state (branch phase)
        - Content causal history (Jones invariant)
        - Temporal ordering (logical timestamp)
        """
        # Compute sender hash from public coherence state
        sender_hash = hashlib.sha256(
            f"{sender_id}:{metadata.get('coherence_state', '')}".encode()
        ).hexdigest()

        # Compute content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Compute Jones invariant from sender's causal history
        causal_history = metadata.get('causal_history', sender_id)
        jones_inv = self.compute_jones_invariant(causal_history)

        # Extract branch phase from metadata or compute from sender_hash
        if 'branch_phase' in metadata:
            branch_phase = complex(metadata['branch_phase'])
        else:
            # Deterministic phase from sender hash
            phase_angle = int(sender_hash[:8], 16) / (16**8) * 2 * np.pi
            branch_phase = np.exp(1j * phase_angle)

        return MessageSignature(
            sender_hash=sender_hash,
            content_hash=content_hash,
            jones_invariant=jones_inv,
            branch_phase=branch_phase,
            timestamp=metadata.get('timestamp', 0.0)
        )

    def verify_message(
        self,
        sender_id: str,
        content: str,
        metadata: Dict,
        local_coherence: float
    ) -> Dict[str, any]:
        """
        Verifies if a message is legitimate or inter-reality spam.

        Returns verification result with confidence score.
        """
        result = {
            'is_spam': False,
            'confidence': 0.0,
            'reason': None,
            'phase_difference': None,
            'jones_consistent': None
        }

        # Step 1: Check local coherence level
        if local_coherence > self.coherence_threshold:
            # High coherence: crosstalk unlikely, but still verify
            result['reason'] = 'high_coherence_regime'
            result['confidence'] = 0.9
        else:
            # Low coherence: crosstalk possible, rigorous verification needed
            result['reason'] = 'low_coherence_regime'
            result['confidence'] = 0.5

        # Step 2: Extract and verify signature
        try:
            msg_sig = self.extract_message_signature(sender_id, content, metadata)
        except Exception as e:
            result['is_spam'] = True
            result['confidence'] = 0.95
            result['reason'] = f'signature_extraction_failed: {str(e)}'
            return result

        # Step 3: Verify Jones invariant consistency (ZEE200 circuit)
        if self.jones_verification:
            # Compute expected Jones invariant from local branch
            local_causal_history = f"{self.local_phase}:{local_coherence}"
            expected_jones = self.compute_jones_invariant(local_causal_history)

            # Check consistency
            jones_ratio = msg_sig.jones_invariant / expected_jones
            jones_phase_diff = np.angle(jones_ratio)
            jones_consistent = abs(jones_phase_diff) < self.phase_tolerance

            result['jones_consistent'] = jones_consistent
            result['jones_phase_diff'] = jones_phase_diff

            if not jones_consistent:
                result['is_spam'] = True
                result['confidence'] = max(result['confidence'], 0.85)
                result['reason'] = 'jones_invariant_mismatch'
                return result

        # Step 4: Verify branch phase consistency
        phase_diff = np.angle(msg_sig.branch_phase / self.local_phase)
        result['phase_difference'] = abs(phase_diff)

        if abs(phase_diff) > self.phase_tolerance:
            # Phase mismatch: message from different Fisher-Rao branch
            result['is_spam'] = True
            result['confidence'] = max(result['confidence'], 0.9)
            result['reason'] = 'inter_reality_phase_mismatch'
            return result

        # Step 5: Check for entropic shell without semantic core (spam pattern)
        if self._detect_entropic_shell_pattern(content, metadata):
            result['is_spam'] = True
            result['confidence'] = max(result['confidence'], 0.8)
            result['reason'] = 'entropic_shell_without_semantic_core'
            return result

        # Message passed all checks
        result['is_spam'] = False
        result['confidence'] = max(result['confidence'], 0.95)
        result['reason'] = 'all_verifications_passed'

        # Cache signature for future reference
        self._sender_cache[sender_id] = msg_sig

        return result

    def _detect_entropic_shell_pattern(
        self,
        content: str,
        metadata: Dict
    ) -> bool:
        """
        Detects pattern of entropic shell without semantic core.

        Heuristics:
        - High formal structure (HTML, headers, links) but low semantic density
        - Generic content with personalized metadata (hijacking pattern)
        - Mismatch between content complexity and sender reputation
        """
        # Simplified heuristic: check for common spam patterns
        spam_indicators = 0

        # Check for excessive formatting without substance
        if content.count('<') > 50 and len(content) < 500:
            spam_indicators += 1

        # Check for generic content with personalized fields
        if '[[NAME]]' in content or '{{user}}' in content.lower():
            spam_indicators += 1

        # Check for suspicious link density
        link_count = content.lower().count('http')
        if link_count > 5 and len(content) < 1000:
            spam_indicators += 1

        # Check metadata-content mismatch
        if metadata.get('intent', '') == 'promotional' and 'unsubscribe' not in content.lower():
            spam_indicators += 1

        return spam_indicators >= 2
