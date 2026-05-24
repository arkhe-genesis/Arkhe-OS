# tools/delta_gen.py
import sys
import hashlib

def generate_delta(from_version, to_version):
    '''Simulates generating an OTA delta update.'''
    print("[OTA-DELTA] Generating delta from " + str(from_version) + " to " + str(to_version) + "...")

    # Mock data
    delta_data = b"MOCK_DELTA_PAYLOAD_101010"
    delta_hash = hashlib.sha3_256(delta_data).hexdigest()

    print("[OTA-DELTA] Delta generated. Size: " + str(len(delta_data)) + " bytes.")
    print("[OTA-DELTA] Checksum (SHA3-256): " + str(delta_hash))

    return delta_hash

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: delta_gen.py <from_version> <to_version>")
        sys.exit(1)

    generate_delta(sys.argv[1], sys.argv[2])
