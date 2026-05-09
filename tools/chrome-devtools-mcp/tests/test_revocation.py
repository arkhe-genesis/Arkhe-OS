from core.identity.consent_revocation_cascade import RevocationCascadeManager

def test_revocation():
    manager = RevocationCascadeManager("did:1")
    manager.register_vc("vc1", {"data": "test"})
    assert manager.verify_longitudinal_continuity("vc1", "hash1") == True

    tombstone = manager.retire_vc_gracefully("vc1", "hash1", "sig")
    assert tombstone is not None
    assert manager.verify_longitudinal_continuity("vc1", "hash1") == True
    assert manager.verify_longitudinal_continuity("vc1", "wrong_hash") == False
