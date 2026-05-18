import pytest
from substrates.substrato_220_proof_of_hallucination import ProofOfHallucinationValidator, SyntheticUniverse

def test_proof_of_hallucination():
    validator = ProofOfHallucinationValidator()
    validator.register_universe("halupedia", parent_universe=None)

    # 1. Valid Article
    validator.universes["halupedia"].add_entity("Goblin King")
    validator.universes["halupedia"].add_event(100.0, "Goblin Coronation")
    validator.universes["halupedia"].define_term("Goblin")

    valid_article = {
        "title": "The Rule of Goblin King",
        "content": "The rule of the <<Goblin>> King.",
        "links": ["Goblin King"],
        "timestamp": 200.0
    }

    is_valid, violations = validator.validate_article("halupedia", valid_article)
    assert is_valid, f"Expected valid article, got violations: {violations}"

    # 2. Broken Internal Link
    invalid_link_article = {
        "title": "Elf War",
        "content": "A story about elves.",
        "links": ["Elf Queen"],
        "timestamp": 300.0
    }
    is_valid, violations = validator.validate_article("halupedia", invalid_link_article)
    assert not is_valid
    assert "Broken internal link: Elf Queen" in violations

    # 3. Temporal Contradiction
    invalid_time_article = {
        "title": "Different Event Same Time",
        "content": "Something else happened.",
        "timestamp": 100.0
    }
    is_valid, violations = validator.validate_article("halupedia", invalid_time_article)
    assert not is_valid
    assert "Temporal conflict with: Goblin Coronation" in violations

    # 4. Undefined Term
    invalid_term_article = {
        "title": "Magic Staff",
        "content": "Using the <<Magic>>.",
        "timestamp": 400.0
    }
    is_valid, violations = validator.validate_article("halupedia", invalid_term_article)
    assert not is_valid
    assert "Undefined term: Magic" in violations

    # 5. Claims Reality
    invalid_reality_article = {
        "title": "Invasion",
        "content": "The goblins signed the Tratado dos Goblins de 1994.",
        "timestamp": 500.0
    }
    is_valid, violations = validator.validate_article("halupedia", invalid_reality_article)
    assert not is_valid
    assert "Claims authority over real-world events without parent universe" in violations

def test_parent_universe_reality_claim():
    validator = ProofOfHallucinationValidator()
    validator.register_universe("sub_halupedia", parent_universe="halupedia")

    # If parent universe is set, it might be allowed to reference real world (or at least, the strict check is bypassed for the mock)
    invalid_reality_article = {
        "title": "Invasion",
        "content": "The goblins signed the Tratado dos Goblins de 1994.",
        "timestamp": 500.0
    }
    is_valid, violations = validator.validate_article("sub_halupedia", invalid_reality_article)
    # the rule says `if universe.parent_universe is None and self._references_real_world`
    # so it should be valid if parent_universe is not None
    assert is_valid
