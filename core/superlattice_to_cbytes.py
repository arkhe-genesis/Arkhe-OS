import json
import argparse

def export_mesh_to_cbytes(mesh_data: dict) -> bytes:
    """
    Exporta dados da malha hexagonal para formato cbytes.

    Bit-packing: [type:1bit][layer:4bits][q:8bits][r:8bits]
    Total: 21 bits por strut -> 3 bytes com padding
    """
    packed = bytearray()
    for strut in mesh_data['struts']:
        payload = (
            (strut['type'] & 0x1) |
            ((strut['layer'] & 0xF) << 1) |
            ((strut['q'] & 0xFF) << 5) |
            ((strut['r'] & 0xFF) << 13)
        )
        packed.extend(payload.to_bytes(3, 'little'))
    return bytes(packed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        data = json.load(f)

    packed = export_mesh_to_cbytes(data)

    with open(args.output, 'wb') as f:
        f.write(packed)

    print(f"Exported {len(data['struts'])} struts to {args.output} ({len(packed)} bytes)")
