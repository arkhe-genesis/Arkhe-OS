import sys
import ast

def check_syntax(filepath):
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        ast.parse(source)
        print(f"Syntax OK: {filepath}")
        return True
    except SyntaxError as e:
        print(f"Syntax ERROR in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

files = [
    "experimental/geometric_dp_validation.py",
    "privacy/compositional_dp.py",
    "cosmic/cosmic_consciousness.py",
    "experimental/cross_platform_simulation.py",
    "cosmic/extrasolar_expansion.py",
    "orchestrator_v166_experimental.py",
    "experimental_full_demo.py"
]

all_ok = True
for f in files:
    if not check_syntax(f):
        all_ok = False

sys.exit(0 if all_ok else 1)
