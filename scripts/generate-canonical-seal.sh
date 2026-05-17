#!/bin/bash
set -euo pipefail

echo "Generating canonical seal..."
COMMIT_HASH=$(git rev-parse HEAD || echo "no-commit")
PHI_C=${1:-0.9999}
TIMESTAMP=$(date -u +%s)
# Mock pubkey hash
PUBKEY_HASH="mock_pubkey_hash_$(date +%s)"

CANONICAL_SEAL=$(echo -n "${COMMIT_HASH}${PHI_C}${TIMESTAMP}${PUBKEY_HASH}" | sha256sum | cut -d' ' -f1)
echo "canonical_seal=${CANONICAL_SEAL}"
