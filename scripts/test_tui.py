import sys
import os
os.environ["ARKHE_SKIP_INTEGRITY"] = "1"
from arkhe_os.cli.tui_audit import draw_tui

mock_files = [
    {"path": "core/parser.py", "phi": 0.94},
    {"path": "api/handler.py", "phi": 0.72},
    {"path": "utils/validator.py", "phi": 0.88},
    {"path": "legacy/deprecated.py", "phi": 0.31},
    {"path": "auth/token.py", "phi": 0.15},
    {"path": "config/settings.py", "phi": 0.55},
    {"path": "quantum/floquet.py", "phi": 0.98},
]

global_phi = sum(item["phi"] for item in mock_files) / len(mock_files)

draw_tui("my-project", "npub1abc", global_phi, mock_files)
print("\n[SUCCESS] TUI executed cleanly using design system.")
