import pytest
import time
from core.ethics.metacognitive_tagging import MetacognitiveTag, LongitudinalEthicsTracker

def test_metacognitive_tag_hashing():
    tag = MetacognitiveTag(
        subject_id="subj-42",
        ledger_entry_hash="abc123hash",
        qualitative_insight="Deep REM recall",
        consent_state=True,
        timestamp_utc=1600000000.0
    )

    tag.compute_hash()
    assert tag.tag_hash != ""
    assert len(tag.tag_hash) == 64 # SHA-256

def test_longitudinal_ethics_tracker():
    tracker = LongitudinalEthicsTracker()

    tag1 = MetacognitiveTag(
        subject_id="subj-42",
        ledger_entry_hash="hash-1",
        qualitative_insight="Session 1 clear",
        consent_state=True,
        timestamp_utc=1600000000.0
    )

    tag2 = MetacognitiveTag(
        subject_id="subj-42",
        ledger_entry_hash="hash-2",
        qualitative_insight="Session 2 clear",
        consent_state=True,
        timestamp_utc=1600001000.0
    )

    tracker.append_tag(tag1)
    tracker.append_tag(tag2)

    assert tracker.verify_longitudinal_continuity("subj-42") is True

def test_longitudinal_ethics_tracker_revoked_consent():
    tracker = LongitudinalEthicsTracker()

    tag1 = MetacognitiveTag(
        subject_id="subj-42",
        ledger_entry_hash="hash-1",
        qualitative_insight="Session 1 clear",
        consent_state=True,
        timestamp_utc=1600000000.0
    )

    tag2 = MetacognitiveTag(
        subject_id="subj-42",
        ledger_entry_hash="hash-2",
        qualitative_insight="Too intense, stopping.",
        consent_state=False, # Revoked
        timestamp_utc=1600001000.0
    )

    tracker.append_tag(tag1)
    tracker.append_tag(tag2)

    # Should be False because consent was revoked in the chain
    assert tracker.verify_longitudinal_continuity("subj-42") is False

def test_longitudinal_ethics_tracker_tampering():
    tracker = LongitudinalEthicsTracker()

    tag1 = MetacognitiveTag(
        subject_id="subj-42",
        ledger_entry_hash="hash-1",
        qualitative_insight="Session 1 clear",
        consent_state=True,
        timestamp_utc=1600000000.0
    )

    tracker.append_tag(tag1)

    # Simulate tampering with the data after the fact
    tag1.consent_state = False

    # Re-verification should fail because the hash no longer matches the modified data
    assert tracker.verify_longitudinal_continuity("subj-42") is False
