#!/usr/bin/env bash
# embedded/install.sh — Embedded .agi handler
set -euo pipefail

PREFIX="${PREFIX:-/opt/arkhe}"
BIN_DIR="$PREFIX/bin"
LIB_DIR="$PREFIX/lib/arkhe"

echo "Installing for Embedded at $PREFIX"
mkdir -p "$BIN_DIR" "$LIB_DIR"
cp -r ../common/*.py "$LIB_DIR/"

cat > "$BIN_DIR/agictl" << 'EOF'
#!/usr/bin/env python3
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
