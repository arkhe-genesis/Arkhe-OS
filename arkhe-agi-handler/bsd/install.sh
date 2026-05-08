#!/usr/bin/env bash
# bsd/install.sh — BSD .agi handler
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local/arkhe}"
USER_MODE="${USER_MODE:-true}"

BIN_DIR="$PREFIX/bin"
LIB_DIR="$PREFIX/lib/arkhe"
SHARE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
ICON_DIR="$SHARE_DIR/icons/hicolor"
MIME_DIR="$SHARE_DIR/mime"
APP_DIR="$SHARE_DIR/applications"

echo "Installing for BSD at $PREFIX"
mkdir -p "$BIN_DIR" "$LIB_DIR"
cp -r ../common/*.py "$LIB_DIR/"

cat > "$BIN_DIR/agictl" << 'EOF'
#!/usr/bin/env python3
"""agictl — ARKHE OS Artifact CLI (BSD)"""
import sys, os, subprocess, json, tarfile
from pathlib import Path

lib = Path(__file__).parent.parent / "lib" / "arkhe"
sys.path.insert(0, str(lib)) if lib.exists() and str(lib) not in sys.path else None

from verify import verify_artifact
from extract import extract_artifact
from manifest import view_manifest

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    action, path = sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None
    if not path or not Path(path).exists():
        sys.exit(1)

    if action == "open":
        if verify_artifact(path):
            extract_artifact(path, f"{path}_extracted")
        else: sys.exit(1)
    elif action == "verify": sys.exit(0 if verify_artifact(path) else 1)
    elif action == "extract":
        out = sys.argv[3] if len(sys.argv)>3 else f"{path}_extracted"
        extract_artifact(path, out)
    elif action == "manifest": view_manifest(path)
    else: sys.exit(1)

if __name__ == "__main__": main()
EOF
chmod +x "$BIN_DIR/agictl"
echo "Done"
