#!/bin/bash
mkdir -p osf_submission_v320_1/proofs
mkdir -p osf_submission_v320_1/results
cp proofs/* osf_submission_v320_1/proofs/
cp results/* osf_submission_v320_1/results/
cp scripts/arkhe_zee200_integration_v320_1/verify_aggregated_proof.py osf_submission_v320_1/
echo "OSF submission package created in osf_submission_v320_1/"
