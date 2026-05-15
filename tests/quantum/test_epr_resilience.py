import pytest
import hashlib

def generate_epr_pair():
    # Simulate entangled photons
    state = "EPR_STATE_(|00>+|11>)"
    return state, state

def sign_block(capsule_id, block_data, epr_state):
    # Simulate quantum signing
    hash_obj = hashlib.sha256()
    hash_obj.update(f"{capsule_id}_{block_data}_{epr_state}".encode())
    return hash_obj.hexdigest()

def test_epr_resilience_capsules():
    block_data = "BLOCK_190"

    # Generate EPR pair
    epr1, epr2 = generate_epr_pair()

    # Capsule 1 signs with EPR1
    sig1 = sign_block("CAPSULE_1", block_data, epr1)

    # Capsule 2 signs with EPR2
    sig2 = sign_block("CAPSULE_2", block_data, epr2)

    # Verify both signatures are valid for the same block and entangled state
    assert sig1 != sig2 # They are different signatures
    assert epr1 == epr2 # They share the same entangled state

    # Verification function would check the state
    def verify(block_data, sig1, sig2, epr_state):
        return (
            sign_block("CAPSULE_1", block_data, epr_state) == sig1 and
            sign_block("CAPSULE_2", block_data, epr_state) == sig2
        )

    assert verify(block_data, sig1, sig2, epr1)
