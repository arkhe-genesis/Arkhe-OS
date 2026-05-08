#!/usr/bin/env bash
# linux/install.sh — Linux .agi handler (XDG/MIME/desktop)

set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local/arkhe}"
USER_MODE="${USER_MODE:-true}"
DISTRO="${DISTRO:-linux-generic}"

BIN_DIR="$PREFIX/bin"
LIB_DIR="$PREFIX/lib/arkhe"
SHARE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
ICON_DIR="$SHARE_DIR/icons/hicolor"
MIME_DIR="$SHARE_DIR/mime"
APP_DIR="$SHARE_DIR/applications"

log() { echo -e "\033[0;34m[LINUX]\033[0m $1"; }
success() { echo -e "\033[0;32m✓\033[0m $1"; }

setup_dirs() {
    mkdir -p "$BIN_DIR" "$LIB_DIR"
    mkdir -p "$ICON_DIR"/{16x16,32x32,48x48,128x128,256x256}/apps
    mkdir -p "$MIME_DIR"/{packages,icons} "$APP_DIR"
}

install_core() {
    log "Installing agictl core..."
    cp -r ../common/*.py "$LIB_DIR/"

    cat > "$BIN_DIR/agictl" << 'EOF'
#!/usr/bin/env python3
"""agictl — ARKHE OS Artifact CLI (Linux)"""
import sys, os, subprocess, json, tarfile
from pathlib import Path

lib = Path(__file__).parent.parent / "lib" / "arkhe"
sys.path.insert(0, str(lib)) if lib.exists() and str(lib) not in sys.path else None

from verify import verify_artifact
from extract import extract_artifact
from manifest import view_manifest

def main():
    if len(sys.argv) < 2:
        print("Usage: agictl [open|verify|extract|manifest] <file.agi>")
        sys.exit(1)

    action, path = sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None
    if not path or not Path(path).exists():
        print(f"Error: {path} not found"); sys.exit(1)

    if action == "open":
        if verify_artifact(path):
            extract_artifact(path, f"{path}_extracted")
            subprocess.run(["xdg-open", f"{path}_extracted"])
        else: sys.exit(1)
    elif action == "verify": sys.exit(0 if verify_artifact(path) else 1)
    elif action == "extract":
        out = sys.argv[3] if len(sys.argv)>3 else f"{path}_extracted"
        extract_artifact(path, out); print(f"✓ {out}")
    elif action == "manifest": view_manifest(path)
    else: print(f"Unknown: {action}"); sys.exit(1)

if __name__ == "__main__": main()
EOF
    chmod +x "$BIN_DIR/agictl"
    success "agictl installed"
}

install_icons() {
    [[ "${SKIP_ICONS:-false}" == "true" ]] && return
    log "Installing icons..."
    for size in 16 32 48 128 256; do
        cp "../common/icons/arkhe-icon-${size}.png" \
           "$ICON_DIR/${size}x${size}/apps/arkhe-agi.png"
    done
    success "Icons installed"
}

register_mime() {
    log "Registering MIME type..."
    cat > "$MIME_DIR/packages/arkhe-agi.xml" << 'EOF'
<?xml version="1.0"?><mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-arkhe-agi">
    <comment>ARKHE OS Artifact</comment>
    <glob pattern="*.agi"/><magic priority="90">
      <match type="string" value="AGI_ARTIFACT_V1" offset="0"/></magic>
    <icon name="arkhe-agi"/></mime-type></mime-info>
EOF
    update-mime-database "$MIME_DIR" 2>/dev/null || true
    success "MIME: application/x-arkhe-agi"
}

register_desktop() {
    log "Creating desktop entry..."
    cat > "$APP_DIR/arkhe-agi.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=ARKHE OS Artifact
Comment=Open, verify, instantiate .agi artifacts
Exec=agictl open %f
Icon=arkhe-agi
MimeType=application/x-arkhe-agi;
Terminal=false
Categories=Development;Utility;
Keywords=AGI;ARKHE;artifact;
EOF
    # Using sed to replace Exec path properly to avoid eval issues if variables are not expanded.
    sed -i "s|Exec=agictl open %f|Exec=$BIN_DIR/agictl open %f|g" "$APP_DIR/arkhe-agi.desktop"

    update-desktop-database "$APP_DIR" 2>/dev/null || true
    success "Desktop entry created"
}

add_context_menu() {
    log "Adding file manager context menu..."
    # Nautilus
    [[ -d "$HOME/.local/share/nautilus/scripts" ]] && {
        cat > "$HOME/.local/share/nautilus/scripts/Verify ARKHE" << 'EOF'
#!/bin/bash
agictl verify "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
EOF
        chmod +x "$HOME/.local/share/nautilus/scripts/Verify ARKHE"
    }
    # Dolphin (KDE)
    [[ -d "$HOME/.local/share/kio/servicemenus" ]] && {
        cat > "$HOME/.local/share/kio/servicemenus/arkhe-agi.desktop" << 'EOF'
[Desktop Entry]
Type=Service;ServiceTypes=KonqPopupMenu/Plugin
MimeType=application/x-arkhe-agi;
Actions=verify;extract;
[Desktop Action verify]
Name=&Verify Integrity
Exec=agictl verify %F
[Desktop Action extract]
Name=E&xtract
Exec=agictl extract %F
EOF
    }
    success "Context menu added"
}

update_env() {
    log "Updating PATH..."
    grep -q "$BIN_DIR" "$HOME/.bashrc" 2>/dev/null || \
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$HOME/.bashrc"
    grep -q "$BIN_DIR" "$HOME/.zshrc" 2>/dev/null || \
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$HOME/.zshrc"

    # Icon cache
    command -v gtk-update-icon-cache &>/dev/null && \
        for d in "$ICON_DIR"/*/; do gtk-update-icon-cache -f -t "$d" 2>/dev/null || true; done
    success "Environment updated"
}

main() {
    log "🐧 Installing for Linux ($DISTRO)"
    setup_dirs; install_core; install_icons
    register_mime; register_desktop; add_context_menu; update_env
    echo ""; success "Linux install complete!"
    echo "  • Run: source ~/.bashrc"; echo "  • Test: agictl --help"
}
main "$@"
