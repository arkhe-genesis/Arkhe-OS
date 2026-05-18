use rusqlite::Result;
use substrato_231_sqlite::{ArkheStore, CanonicalToken, VerifiedProposition, EvidenceRecord, canonical_hash, now_timestamp};

#[test]
fn test_insert_and_get_token() -> Result<()> {
    let store = ArkheStore::new(":memory:")?;
    let payload = serde_json::json!({
        "origin": "test_origin",
        "signal": "test"
    });
    let payload_string = serde_json::to_string(&payload).unwrap();
    let header = canonical_hash(payload_string.as_bytes());
    let ts = now_timestamp();
    let token = CanonicalToken {
        header: header.clone(),
        identity: "test_identity".into(),
        semantics: "test_semantics".into(),
        payload_json: payload_string,
        seal: canonical_hash(format!("{}:test_identity:{}", header, ts).as_bytes()),
        timestamp: ts,
    };
    store.insert_token(&token)?;

    let fetched = store.get_token_by_seal(&token.seal)?.unwrap();
    assert_eq!(fetched.header, token.header);
    assert_eq!(fetched.identity, token.identity);
    Ok(())
}

#[test]
fn test_propositions_and_stats() -> Result<()> {
    let store = ArkheStore::new(":memory:")?;

    let prop1 = VerifiedProposition {
        id: None,
        source_hash: canonical_hash(b"prop1"),
        phi_c: 0.95,
        violations: "[]".into(),
        is_valid: true,
        verified_at: now_timestamp(),
    };
    store.insert_verified_proposition(&prop1)?;

    let prop2 = VerifiedProposition {
        id: None,
        source_hash: canonical_hash(b"prop2"),
        phi_c: 0.85,
        violations: serde_json::to_string(&vec!["error"]).unwrap(),
        is_valid: false,
        verified_at: now_timestamp(),
    };
    store.insert_verified_proposition(&prop2)?;

    let high_phi = store.get_propositions_above_phi(0.9, 10)?;
    assert_eq!(high_phi.len(), 1);
    assert_eq!(high_phi[0].phi_c, 0.95);

    let stats = store.stats()?;
    assert_eq!(stats.prop_count, 2);
    assert!((stats.avg_phi - 0.9).abs() < 1e-6);

    Ok(())
}

#[test]
fn test_evidence() -> Result<()> {
    let store = ArkheStore::new(":memory:")?;
    let data = b"secret data";
    let evidence = EvidenceRecord {
        hash: canonical_hash(data),
        data_blob: data.to_vec(),
        timestamp: now_timestamp(),
    };

    store.store_evidence(&evidence)?;

    let fetched = store.get_evidence(&evidence.hash)?.unwrap();
    assert_eq!(fetched.data_blob, data.to_vec());

    Ok(())
}
