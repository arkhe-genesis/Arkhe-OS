#!/usr/bin/env python3
# scripts/simulate_cosmic_federation.py
# Simulates a federated consensus round with 5 surveys and ZK proof verification.

import json
import subprocess
import os
import time
import hashlib

def run_node_script(survey_id, p_occ):
    """Calls the Node.js proof generation script."""
    result = subprocess.run(
        ["node", "scripts/generate_cosmic_pocc_proof.cjs", survey_id, str(p_occ)],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error generating proof for {survey_id}: {result.stderr}")
        return None
    try:
        # Extract the JSON part from the output
        stdout = result.stdout.strip()
        json_start = stdout.find('{')
        if json_start == -1:
            print(f"No JSON found in output for {survey_id}")
            return None
        json_str = stdout[json_start:]
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON for {survey_id}: {e}")
        print(f"Raw output: {result.stdout}")
        return None

class MockCosmicDAOFederated:
    """Mock implementation of the Solidity contract logic."""
    def __init__(self):
        self.proofs = {}
        self.p_min_threshold = 100 # 1e-122 scaled
        self.current_approvals = 0
        self.current_rejections = 0
        self.consensus_reached = False

    def submit_proof(self, survey_proof):
        # Verification logic (mocking the verifier.verifyProof call)
        # In this simulation, if is_valid signal is "1", we accept it
        if survey_proof['publicSignals'][0] == "1":
            self.proofs[survey_proof['surveyId']] = {
                'verified': True,
                'p_occ_commitment': survey_proof['publicSignals'][1]
            }
            print(f"✅ Proof from {survey_proof['surveyId']} verified and recorded.")
            return True
        else:
            print(f"❌ Proof from {survey_proof['surveyId']} REJECTED.")
            return False

    def vote(self, survey_id, approve=True):
        if survey_id in self.proofs and self.proofs[survey_id]['verified']:
            if approve:
                self.current_approvals += 1
            else:
                self.current_rejections += 1
            print(f"🗳️  {survey_id} voted {'APPROVE' if approve else 'REJECT'}.")

            if self.current_approvals + self.current_rejections >= 3:
                self.finalize_consensus()
        else:
            print(f"⚠️  {survey_id} cannot vote without a verified proof.")

    def finalize_consensus(self):
        total = self.current_approvals + self.current_rejections
        if total == 0: return
        approval_rate = (self.current_approvals * 100) / total
        if approval_rate >= 66:
            self.consensus_reached = True
            print(f"🌟 CONSENSUS REACHED! New P_min threshold established.")
        else:
            print(f"💔 CONSENSUS FAILED. Approval rate {approval_rate}% below threshold.")

def simulate():
    print("🚀 Starting Federated Cosmic Validation Simulation...")
    contract = MockCosmicDAOFederated()

    # 1. Generate synthetic data for 5 surveys
    surveys = {
        "DESI": 3.2e-121,
        "Euclid": 2.8e-121,
        "Planck": 1.0e-120,
        "Roman": 3.5e-121,
        "Vera Rubin": 3.1e-121
    }

    # 2. Submit proofs and vote
    for name, p_occ in surveys.items():
        proof = run_node_script(name, p_occ)
        if proof:
            if contract.submit_proof(proof):
                contract.vote(name, approve=True)

    print(f"\n--- Round Results ---")
    print(f"Approvals: {contract.current_approvals}")
    print(f"Consensus: {'SUCCESS' if contract.consensus_reached else 'FAILURE'}")

    # 3. Test Malicious Survey (Forged Proof)
    print("\n😈 Simulating Malicious Survey (MalicSurvey)...")
    # A malicious survey might try to submit a proof with is_valid="0" or invalid signals
    # Simulate rejection based on forged p_occ (mocking the circuit check)
    malicious_p_occ = 1e-125 # Below threshold
    malicious_proof = run_node_script("MalicSurvey", malicious_p_occ)
    if malicious_proof:
        # Simulate circuit failure for values below threshold
        if malicious_p_occ < 1e-122:
             malicious_proof['publicSignals'][0] = "0" # Rejection by verifier

        contract.submit_proof(malicious_proof)

if __name__ == "__main__":
    simulate()
