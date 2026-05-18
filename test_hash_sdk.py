import pytest
import time
from substrate_202.sdk.interlayer_hash_protocol import (
    CICS_TXN_HashEncoder, LogicProof_HashEncoder, Intention_HashEncoder, MetaVerification_HashEncoder,
    InterLayerHashEnvelope, InterLayerHashValidator
)

def test_hash_encoding_and_validation():
    # 1. Encode CICS TXN
    cics_hash = CICS_TXN_HashEncoder.encode(
        "TXN-001", "ACC1", "ACC2", 100.0, time.time(), "audit_hash", True
    )
    assert InterLayerHashValidator.validate_canonical_hash(cics_hash)[0] == True

    # 2. Encode Logic Proof
    logic_hash = LogicProof_HashEncoder.encode(
        cics_hash.payload_hash, "prop", ["step1"], True, True
    )
    assert InterLayerHashValidator.validate_canonical_hash(logic_hash)[0] == True

    # 3. Create Envelopes
    env1 = InterLayerHashEnvelope("mainframe_acid", "beaver_logic", cics_hash, sequence_number=1)
    env2 = InterLayerHashEnvelope("beaver_logic", "token_arkhe_intention", logic_hash, sequence_number=2)

    assert InterLayerHashValidator.validate_envelope(env1)[0] == True

    # 4. Verify Chain
    assert InterLayerHashValidator.verify_hash_chain([env1, env2]) == True

    # Break chain
    bad_logic_hash = LogicProof_HashEncoder.encode(
        "wrong_hash", "prop", ["step1"], True, True
    )
    bad_env2 = InterLayerHashEnvelope("beaver_logic", "token_arkhe_intention", bad_logic_hash, sequence_number=2)
    assert InterLayerHashValidator.verify_hash_chain([env1, bad_env2]) == False
