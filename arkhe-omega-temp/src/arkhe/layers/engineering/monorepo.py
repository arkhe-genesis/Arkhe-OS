# src/arkhe/layers/engineering/monorepo.py
import os
from .error_standardization import ArkheError

def verify_monorepo_structure(root: str):
    required_dirs = [
        "src/arkhe/layers",
        "src/arkhe/layers/engineering",
        "tests/test_layers",
        "locales/en-US",
        "arkp-core",
        "arkp-registry",
    ]
    for d in required_dirs:
        if not os.path.exists(os.path.join(root, d)):
            raise ArkheError("E007", f"Missing directory: {d}")
    return True
