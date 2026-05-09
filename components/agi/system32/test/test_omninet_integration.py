# test_omninet_integration.py
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'runtime', 'quantum')))

from omninet_integration import OmniNetMessage, OmniNetMessageType

def test_omninet_message_signature():
    msg = OmniNetMessage(
        msg_id="test_msg_1",
        msg_type=OmniNetMessageType.INTENT_BROADCAST,
        src_node="node_A",
        dst_node="node_B",
        payload={"data": "test"}
    )

    secret_key = "test_secret"
    signature = msg.compute_signature(secret_key)
    msg.signature = signature

    assert msg.verify_signature(secret_key) is True
    assert msg.verify_signature("wrong_secret") is False
