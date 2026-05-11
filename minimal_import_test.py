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
    "orchestrator/mission_pipeline_compositional.py",
    "cosmic/autonomous_alert_response.py",
    "cosmic/extrasolar_network_routing.py",
    "orchestrator_v167_production.py",
    "production_full_demo.py"
]

all_ok = True
for f in files:
    if not check_syntax(f):
        all_ok = False

sys.exit(0 if all_ok else 1)
