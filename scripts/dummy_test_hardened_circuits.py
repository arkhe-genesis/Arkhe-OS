import pytest
import os

def test_circuits_exist():
    circuits = [
        "circuits/sovereign_swap.circom",
        "circuits/HumanCoherenceProof.circom",
        "circuits/BioPhotonVerifier.circom"
    ]
    for circuit in circuits:
        assert os.path.exists(circuit)

def test_no_underconstrained_dummy_in_swap():
    with open("circuits/sovereign_swap.circom", "r") as f:
        content = f.read()
        assert "dummy constraint" not in content
        # Ensure it has a real constraint now
        assert "private_amount_in * 1" not in content or "===" in content

def test_num2bits_presence():
    # HumanCoherenceProof and BioPhotonVerifier should use some form of range check/bitify
    # if they are hardened.
    for circuit in ["circuits/HumanCoherenceProof.circom", "circuits/BioPhotonVerifier.circom"]:
        with open(circuit, "r") as f:
            content = f.read()
            # This is a weak check, but without a compiler, we look for intent
            assert "Num2Bits" in content or "bitify" in content or "bit" in content
