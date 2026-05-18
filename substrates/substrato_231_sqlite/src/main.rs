use rusqlite::Result;
use substrato_231_sqlite::{ArkheStore, CanonicalToken, VerifiedProposition, EvidenceRecord, canonical_hash, now_timestamp};

fn main() -> Result<()> {
    println!("🏛️ ARKHE SQLite Canonical Store — Substrato 231");
    let store = ArkheStore::new("/tmp/agi-brasil.db")?;

    // 1. Criar e armazenar um Token Arkhe
    let payload = serde_json::json!({
        "origin": "cosmic_ear",
        "signal_type": "SIGINT",
        "frequency_mhz": 1420.4
    });
    let payload_string = serde_json::to_string(&payload).unwrap();
    let header = canonical_hash(payload_string.as_bytes());
    let token = CanonicalToken {
        header: header.clone(),
        identity: "cosmic_ear_001".into(),
        semantics: "signal_collected".into(),
        payload_json: payload_string,
        seal: canonical_hash(format!("{}:cosmic_ear_001:{}", header, now_timestamp()).as_bytes()),
        timestamp: now_timestamp(),
    };
    store.insert_token(&token)?;
    println!("✅ Token armazenado: {}", token.seal);

    // 2. Armazenar uma proposição verificada
    let prop = VerifiedProposition {
        id: None,
        source_hash: canonical_hash(b"exemplo"),
        phi_c: 0.92,
        violations: serde_json::to_string(&vec!["confidence_mismatch"]).unwrap(),
        is_valid: false,
        verified_at: now_timestamp(),
    };
    store.insert_verified_proposition(&prop)?;
    println!("✅ Proposição armazenada, Φ_C={}", prop.phi_c);

    // 3. Armazenar evidência binária
    let data = b"Dados confidenciais de inteligencia";
    let evidence = EvidenceRecord {
        hash: canonical_hash(data),
        data_blob: data.to_vec(),
        timestamp: now_timestamp(),
    };
    store.store_evidence(&evidence)?;
    println!("✅ Evidência armazenada, hash={}", evidence.hash);

    // 4. Estatísticas
    let stats = store.stats()?;
    println!("📊 Tokens: {}, Proposições: {}, Evidências: {}, Φ_C médio: {:.4}",
             stats.token_count, stats.prop_count, stats.evidence_count, stats.avg_phi);

    println!("📜 Canonical Seal: {}", canonical_hash(b"substrate_231_sqlite_rust"));
    Ok(())
}
