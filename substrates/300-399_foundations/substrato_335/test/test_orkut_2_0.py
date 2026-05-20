import pytest
import sys
import os

# Manipulate sys.path to be able to import the module from a directory with hyphens/numbers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orkut_2_0 import (
    ResearcherProfile, Scrap, TemporalChain, Community, GHOST, GAP_MAX
)

def test_researcher_profile_invariants():
    profile = ResearcherProfile(
        orcid="0000-0000-0000-0001",
        arkhe_token="token_1",
        name="Test Profile",
        institution="Test Inst",
        research_area="Test Area"
    )
    assert profile.phi_c_reputation == GHOST

    # Test Gap Max enforcement
    profile.update_reputation(0.5)
    assert profile.phi_c_reputation < GAP_MAX

def test_community_moderation():
    chain = TemporalChain()
    profile1 = ResearcherProfile("001", "tok1", "Alice", "Inst", "Area")
    profile2 = ResearcherProfile("002", "tok2", "Bob", "Inst", "Area")
    profile3 = ResearcherProfile("003", "tok3", "Charlie", "Inst", "Area")

    community = Community("c1", "Test Comm", "Desc")
    community.join(profile1)

    scrap = Scrap(author_orcid=profile1.orcid, content="Test content")
    community.post_scrap(scrap, chain)

    # Moderate the scrap down
    votes = [(profile2, False), (profile3, False)]
    community.moderate_content(scrap, votes)

    assert scrap.visibility_score < 1.0

def test_temporal_chain_anchoring():
    chain = TemporalChain()
    scrap = Scrap(author_orcid="001", content="Hash test")
    hash_val = chain.anchor_content(scrap)

    assert hash_val is not None
    assert len(hash_val) == 64 # SHA3-256 length
