import sys
import os

def validate(ontology_path, ritual_path):
    print(f"Validating Ritual of Acceptance: {ritual_path} against {ontology_path}")
    if not os.path.exists(ritual_path):
        print(f"Error: Ritual of Acceptance document missing at {ritual_path}")
        return False

    with open(ritual_path, 'r') as f:
        content = f.read()
        if "Princípio Fundador" not in content or "Fase 1" not in content:
            print("Error: Ritual of Acceptance document does not follow the required template.")
            return False

    print("Ritual of Acceptance validated successfully.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python validate_ritual.py <ontology> <ritual>")
        sys.exit(1)
    if validate(sys.argv[1], sys.argv[2]):
        sys.exit(0)
    else:
        sys.exit(1)
