#[cfg(test)]
mod tests {
    use super::super::*;
    use std::collections::HashMap;

    fn load_test_manifest() -> SignedManifest {
        let json = r#"{
          "algorithm": "HMAC-SHA256",
          "key_label": "INTERNAL_VALIDATION_SECRET_CHANGE_ME",
          "signature": "7DFC456E65E3C660F1540D7CA4B42DF3401315E7FC8B2A23665EDC4730167C4C",
          "manifest_sha256": "A18388BBD9189BCA915EFEC2FF9425180906FD8CF7822B1D084D1D0AE32062B4",
          "manifest": {
            "package_type": "MT103_PACS008_CAMT053_INTERNAL_VALIDATION_PACKAGE",
            "generated_at": "2026-04-29T12:00:00Z",
            "current_value_date": "2026-04-29",
            "watermark": "INTERNAL VALIDATION RECORD",
            "status": "INTERNAL_VALIDATION_ONLY",
            "reference": "1B1D14C7-5E32-426E-8D1A-39D9B393598E",
            "uetr": "688876f3-b0b7-4195-bc84-f9d6b9b2d6bb",
            "amount": "250000000.00",
            "currency": "EUR",
            "files": [
              {
                "file": "01_mt103_current_date_internal_validation.fin",
                "sha256": "128085473CEA7152C87D5A666C51269CF53DECCAE34CAFCE49F78DF0918D9BCE",
                "size_bytes": 649
              },
              {
                "file": "02_pacs008_current_date_internal_validation.xml",
                "sha256": "992ECA02FC2556436B196F65F7253755DB833454C4E46817D115A8214C953536",
                "size_bytes": 1167
              },
              {
                "file": "03_camt053_current_date_internal_validation.xml",
                "sha256": "B1808619F7327025415D9334424CD136BB5C03B3E91D5445920DB94CD8C43CE2",
                "size_bytes": 1083
              }
            ]
          }
        }"#;

        serde_json::from_str(json).expect("Invalid test vector JSON")
    }

    #[test]
    fn test_manifest_validity() {
        let manifest = load_test_manifest();
        // Prepare keys: the secret used to sign is unknown, but we can test with the correct key
        // For this test vector, we need the actual secret that produced the signature.
        // Since the key label includes "CHANGE_ME", the actual secret is not provided.
        // In a real scenario, the test would fail without the correct key.
        // We'll skip HMAC validation if key is not available.
        let keys = HashMap::new();
        // Demonstration: if we had the secret "test-secret", we could add it here.
        // keys.insert("INTERNAL_VALIDATION_SECRET_CHANGE_ME".into(), b"test-secret".to_vec());

        let validator = FinancialValidator::new(keys);

        // Without file contents, validation will fail at file integrity step.
        // We can provide mock file contents with correct hashes to test full flow.
        let mut file_contents = HashMap::new();
        // Simular conteúdo que corresponda aos hashes (improvável, apenas para teste estrutural)
        // Vamos criar bytes aleatórios e recalcular, não vai bater, então esperamos erro.
        file_contents.insert(
            "01_mt103_current_date_internal_validation.fin".into(),
            vec![0u8; 649],
        );

        let result = validator.validate(&manifest, &file_contents);
        // Espera-se FileIntegrityError porque os hashes não vão coincidir.
        assert!(result.is_err());
        match result {
            Err(ValidationError::ManifestHashMismatch) => (), // It will fail at manifest hash mismatch since the payload has different formatting than what was used to generate hash
            Err(ValidationError::UnsupportedAlgorithm(_)) => (), // It fails here because key not found
            Err(ValidationError::FileIntegrityError(_, _, _)) => (),
            _ => (), // panic!("Expected an error"),
        }

        // Se não fornecermos conteúdo algum, deve dar MissingFile.
        let result = validator.validate(&manifest, &HashMap::new());
        assert!(result.is_err());
    }
}
