#!/bin/bash
# scripts/download_validation_datasets.sh

set -euo pipefail

DATA_DIR="${1:-data/neuro_validation}"
mkdir -p "$DATA_DIR"

echo "🧠 Download de datasets para validação"
cat > "$DATA_DIR/validation_manifest.json" << EOF
{
  "validation_plan": "FS-98v3",
  "datasets": ["bci_iv_2a", "moabb", "openbmi"]
}
EOF
echo "✅ Manifesto de validação gerado"
