import yaml
import sys
import hashlib

def validate_schema(file_path):
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    if data.get("kind") != "OntologicalAtlas":
        print(f"Error: {file_path} is not an OntologicalAtlas.")
        sys.exit(1)

    spec = data.get("spec", {})
    eras = spec.get("eras", [])
    substrates = spec.get("substrates", [])

    if len(eras) != 10:
        print(f"Warning: Expected 10 eras, found {len(eras)}.")

    print("Ontological validation passed.")
    print("Odometer:", data.get("metadata", {}).get("odometer", "unknown"))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_linearidade.py <schema.yaml>")
        sys.exit(1)
    validate_schema(sys.argv[1])
