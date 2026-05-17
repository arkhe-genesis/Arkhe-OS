import sys
import os
import time

sys.path.append(os.path.abspath("./arkhe_evm_bridge"))

try:
    from arkhe_evm_bridge import ArkheEVMBridge
except ImportError as e:
    print(f"Failed to import ArkheEVMBridge: {e}")
    sys.exit(1)

def test_encode_decode():
    bridge = ArkheEVMBridge()
    substrate_id = "241+∞"
    canonical_seal = "0x4b854d6a61dab3a5dd8d5ede402d72eac201409d6ee478f767083da3515621b5"
    dummy_signature = "0x" + "00" * 65  # 65-byte ECDSA placeholder

    badge_key = bridge.generate_badge_key(substrate_id, canonical_seal, int(time.time()))
    calldata = bridge.encode_anchor_calldata(badge_key, dummy_signature)
    decoded = bridge.decode_anchor_calldata(calldata)
    assert decoded['badge_key'] == badge_key

print("test_encode_decode OK")
