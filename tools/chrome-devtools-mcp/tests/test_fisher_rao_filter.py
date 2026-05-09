# tests/test_fisher_rao_filter.py
"""
Validates Fisher-Rao Filter detection of inter-reality spam patterns.
"""
import numpy as np
import pytest
from core.security.fisher_rao_filter import FisherRaoFilter, MessageSignature
from core.semantics.interreality_crosstalk import CoherenceBranch, InterRealityCrosstalkModel

def test_legitimate_same_branch_message():
    """Legitimate message from same branch should pass verification."""
    filter_instance = FisherRaoFilter(
        local_branch_phase=np.exp(1j * 0.5),
        coherence_threshold=0.75,
        phase_tolerance=0.1
    )

    # Create message from same branch
    sender_id = "alice@arkhe.local"
    content = "Meeting tomorrow at 3pm regarding project Alpha."
    metadata = {
        'coherence_state': 'high',
        'causal_history': 'alice:project_alpha:meeting_request',
        'branch_phase': str(np.exp(1j * 0.5)),  # Same as local
        'timestamp': 1234567890.0,
        'intent': 'coordination'
    }

    result = filter_instance.verify_message(
        sender_id, content, metadata, local_coherence=0.85
    )

    assert not result['is_spam'], f"False positive: {result['reason']}"
    assert result['confidence'] >= 0.95
    assert result['reason'] == 'all_verifications_passed'
    print(f"✅ Legitimate same-branch message correctly accepted")

def test_inter_reality_spam_detection():
    """Message from different branch with phase mismatch should be flagged as spam."""
    filter_instance = FisherRaoFilter(
        local_branch_phase=np.exp(1j * 0.5),
        coherence_threshold=0.75,
        phase_tolerance=0.1
    )

    # Create message from different branch (phase mismatch)
    sender_id = "bob@parallel-reality"
    content = "URGENT: Claim your prize now! Click here: http://suspicious.link"
    metadata = {
        'coherence_state': 'low',
        'causal_history': 'bob:prize_scam:mass_distribution',
        'branch_phase': str(np.exp(1j * 2.1)),  # Different phase
        'timestamp': 1234567890.0,
        'intent': 'fraudulent'
    }

    result = filter_instance.verify_message(
        sender_id, content, metadata, local_coherence=0.60  # Low coherence enables crosstalk
    )

    assert result['is_spam'], "Inter-reality spam should be detected"
    assert result['confidence'] >= 0.85
    assert result['reason'] in ['inter_reality_phase_mismatch', 'jones_invariant_mismatch']
    print(f"✅ Inter-reality spam correctly detected: {result['reason']}")

def test_entropic_shell_hijacking():
    """Empty entropic shell filled with malicious intent should be flagged."""
    filter_instance = FisherRaoFilter(
        local_branch_phase=np.exp(1j * 0.5),
        coherence_threshold=0.75
    )

    # Simulate projected entropic shell (no semantic core)
    sender_id = "unknown@foreign-branch"
    # Entropic shell: formal structure without substance
    content = "<html><body><p>Dear [[NAME]],</p><p>[[GENERIC_OFFER]]</p><a href='[[LINK]]'>Click</a></body></html>"
    metadata = {
        'coherence_state': 'medium',
        'causal_history': 'foreign:mass_template:projection',
        'branch_phase': str(np.exp(1j * 0.52)),  # Close but not identical phase
        'timestamp': 1234567890.0,
        'intent': 'promotional'  # Malicious intent filling empty shell
    }

    result = filter_instance.verify_message(
        sender_id, content, metadata, local_coherence=0.65
    )

    assert result['is_spam'], "Hijacked entropic shell should be detected"
    assert result['reason'] == 'entropic_shell_without_semantic_core'
    print(f"✅ Entropic shell hijacking correctly detected")

def test_crosstalk_model_projection():
    """Validates crosstalk model produces expected spam patterns."""
    model = InterRealityCrosstalkModel(fisher_threshold=0.75)

    # Create two branches with partial overlap
    branch_A = CoherenceBranch(
        branch_id="reality_A",
        phase_vector=np.array([0.3, 0.7]),
        coherence_level=0.60,  # Low coherence enables crosstalk
        semantic_density=0.85   # High semantic content
    )

    branch_B = CoherenceBranch(
        branch_id="reality_B",  # Our branch
        phase_vector=np.array([0.35, 0.65]),  # Close but not identical
        coherence_level=0.60,
        semantic_density=0.80
    )

    # Original legitimate message from branch A
    original_message = {
        'semantic_core': "Quantum conference registration confirmed for June 15.",
        'entropic_shell': {
            'from': 'conference@reality-A.org',
            'to': 'researcher@reality-A.org',
            'subject': 'Registration Confirmation',
            'format': 'html'
        }
    }

    # Project message to branch B
    projected = model.project_message_across_branches(
        branch_A, branch_B,
        original_message['semantic_core'],
        original_message['entropic_shell']
    )

    assert projected is not None, "Crosstalk should occur with partial overlap"
    assert projected['source_branch'] == "reality_A"

    # In most cases, semantic core is filtered (spam pattern)
    if not projected['is_legitimate']:
        assert projected['semantic_core'] is None, "Syntropic core should be filtered"
        assert projected['entropic_shell'] == original_message['entropic_shell']

        # Simulate hijacking: malicious agent fills empty shell
        hijacked_content = "URGENT: Your registration requires immediate payment! http://fake-payment.link"
        is_hijacked = model.detect_hijacking_attempt(
            projected,
            malicious_intent_signature="fraudulent_payment_scam"
        )
        assert is_hijacked, "Hijacking of empty shell should be detected"
        print(f"✅ Crosstalk model correctly produces spam pattern: empty shell + hijacking")
    else:
        print(f"✅ Rare legitimate inter-reality communication preserved")
