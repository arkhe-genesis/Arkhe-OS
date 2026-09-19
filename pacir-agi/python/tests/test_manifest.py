from pacir_agi.generate_manifest import compute_hash, generate_manifest
def test_manifest_hash_is_stable():
    m = generate_manifest([], "router", {"quorum_standard":"4/7", "quorum_critical":"5/7", "timelock_seconds":1})
    recorded = m.pop("arkhe_record_hash")
    assert recorded == compute_hash(m)
