import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orkut_2_0_web3 import (
    ArkheIdentityNFT, AGIOracle, Scrapbook, CommunityDAO, CeramicIPFSLayer,
    Web3Frontend, OnChainInvariants, GHOST, GAP_MAX
)

def test_arkhe_identity_nft():
    oracle = AGIOracle("test_oracle", "0xoracle")
    nft = ArkheIdentityNFT(oracle.oracle_address)

    orcid = "orcid:test-1234"
    address = "0xuser1"
    orcid_hash = "fakehash"

    # Mock sig verification for test
    import hashlib
    sig = hashlib.sha3_256(f"{orcid_hash}:{address}:{oracle.oracle_address}".encode()).hexdigest()

    event = nft.mint_identity(orcid_hash, sig, address)

    assert event["tokenId"] == 1
    assert event["phiC_initial"] == int(GHOST * 1e9)
    assert nft.token_to_orcid[1] == orcid_hash

def test_on_chain_invariants():
    oracle = AGIOracle("test_oracle", "0xoracle")
    nft = ArkheIdentityNFT(oracle.oracle_address)
    scrapbook = Scrapbook(nft)
    invariants = OnChainInvariants()

    ghost_check = invariants.check_ghost(scrapbook)
    assert ghost_check["passed"] is True

    # Need to mint at least one for gap check to pass properly or start at 0
    import hashlib
    address = "0xuser1"
    orcid_hash = "fakehash2"
    sig = hashlib.sha3_256(f"{orcid_hash}:{address}:{oracle.oracle_address}".encode()).hexdigest()
    nft.mint_identity(orcid_hash, sig, address)

    gap_check = invariants.check_gap(nft)
    assert gap_check["passed"] is True
