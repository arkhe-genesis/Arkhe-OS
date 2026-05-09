import sys
import os

# Ensure we can import from runtime/quantum
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../runtime/quantum')))

from rcp_v2_engine import RetrocausalChannel8Bit, QHTTPRetrocausalTransport

def test_retrocausal_channel():
    print("Testing RetrocausalChannel8Bit fidelity...")
    ch = RetrocausalChannel8Bit()
    # Test multiple bytes to ensure fidelity
    bytes_to_test = [0x00, 0xFF, 0xAA, 0x55]
    for byte_val in bytes_to_test:
        decoded, fidelity = ch.transmit_byte(byte_val, n_shots=50)
        assert decoded == byte_val, f"Mismatch: expected {byte_val}, got {decoded}"
        assert fidelity >= 0.8, f"Fidelity too low for {byte_val}: {fidelity}"
        print(f"Byte {byte_val:02x} transmitted successfully with fidelity {fidelity:.2f}")

def test_qhttp_transport():
    print("Testing QHTTPRetrocausalTransport...")
    ch = RetrocausalChannel8Bit()
    transport = QHTTPRetrocausalTransport("node_A", ch)
    message = "HELLORCP"
    packets = transport.send_retrocausal_message("node_B", message)

    assert len(packets) == len(message)
    decoded_message = ""
    for packet in packets:
        decoded_byte, fidelity = transport.receive_retrocausal_byte(packet)
        decoded_message += chr(decoded_byte)

    assert decoded_message == message, f"Mismatch: expected {message}, got {decoded_message}"
    stats = transport.get_stats()
    assert stats['avg_fidelity'] >= 0.8, f"Average fidelity too low: {stats['avg_fidelity']}"
    print(f"Message '{message}' transmitted successfully. Stats: {stats}")

if __name__ == '__main__':
    test_retrocausal_channel()
    test_qhttp_transport()
    print("All fidelity tests passed.")
