#!/bin/bash
# run_verifiable_pipeline.sh
# Executa pipeline completo: Tracks 1-3 → GTZK proofs → agregação → verificação

set -e  # Exit on error

echo "🔐 ARKHE OS v∞.320.1 — Verifiable Experimental Pipeline"
echo "========================================================"

# 1. Executar Tracks 1-3 e gerar instruções GTZK
echo -e "\n[1/4] Executing Track 1: Mass Scaling..."
python scripts/arkhe_zee200_integration_v320_1/track1_gtzk_wrapper.py --input results/track1_raw.json --output results/track1_gtzk.json

echo -e "\n[2/4] Executing Track 2: Intention Coupling..."
python scripts/arkhe_zee200_integration_v320_1/track2_gtzk_wrapper.py --input results/track2_raw.json --output results/track2_gtzk.json

echo -e "\n[3/4] Executing Track 3: Octonionic Associator..."
python scripts/arkhe_zee200_integration_v320_1/track3_gtzk_wrapper.py --input results/track3_raw.json --output results/track3_gtzk.json

# 2. Agregar provas recursivamente
echo -e "\n[4/4] Aggregating proofs via Merkle tree..."
python scripts/arkhe_zee200_integration_v320_1/recursive_aggregation.py \
  --track1 results/track1_gtzk.json \
  --track2 results/track2_gtzk.json \
  --track3 results/track3_gtzk.json \
  --output proofs/orch_or_aggregated_v320_1.json

# 3. Verificar prova agregada (simulação de validador independente)
echo -e "\n✅ Verifying aggregated proof..."
python scripts/arkhe_zee200_integration_v320_1/verify_aggregated_proof.py \
  --proof proofs/orch_or_aggregated_v320_1.json \
  --verification_key proofs/verification_key.json \
  --track-results results/ \
  --output verification_report.json

# 4. Submeter root hash ao OCTRA (simulado)
ROOT_HASH=$(jq -r '.root_hash' proofs/orch_or_aggregated_v320_1.json)
echo -e "\n📤 Submitting to OCTRA: root_hash=${ROOT_HASH:0:16}..."

echo -e "\n🎉 Pipeline complete. Verification report: verification_report.json"
echo "🔗 Root hash for OCTRA: ${ROOT_HASH}"
