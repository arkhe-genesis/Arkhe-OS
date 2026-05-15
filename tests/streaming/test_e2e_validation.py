import pytest
from arkhe_streaming.platforms.instagram import InstagramLiveAdapter
from arkhe_streaming.platforms.kick import KickStreamAdapter
from arkhe_streaming.platforms.trovo import TrovoStreamAdapter
from arkhe_streaming.security.vault import CredentialsVault, OAuth2Client
from arkhe_streaming.security.hsm_pqc import HSMPQCSigner

def test_vault_and_hsm():
    vault = CredentialsVault()
    oauth = OAuth2Client("client123", "secret")
    token = oauth.fetch_credentials("instagram")
    vault.store_token("instagram", token)

    assert vault.get_token("instagram") == "mock_oauth_token_for_instagram_client123"

    hsm = HSMPQCSigner()
    payload = b"stream_segment_1"
    sig = hsm.sign_payload(payload)
    assert "PQC-DILITHIUM" in sig
    assert hsm.verify_signature(payload, sig) == True

def test_platforms_e2e_coherence():
    # Instagram
    ig = InstagramLiveAdapter("mock_ig_token")
    assert ig.connect() == True
    ig_coh = ig.validate_stream()
    assert 0.85 <= ig_coh <= 0.95

    # Kick
    kick = KickStreamAdapter("mock_kick_token")
    assert kick.connect() == True
    kick_coh = kick.validate_stream()
    assert 0.90 <= kick_coh <= 0.98

    # Trovo
    trovo = TrovoStreamAdapter("mock_trovo_token")
    assert trovo.connect() == True
    trovo_coh = trovo.validate_stream()
    assert 0.88 <= trovo_coh <= 0.97
