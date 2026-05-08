#!/usr/bin/env bash
# macos/install.sh — macOS .agi handler (LaunchServices/UTI)

set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local/arkhe}"
APP_SUPPORT="$HOME/Library/Application Support/ARKHE"
BIN_DIR="$PREFIX/bin"; LIB_DIR="$PREFIX/lib/arkhe"
ICONS_DIR="$APP_SUPPORT/Icons"; UTI_DIR="$APP_SUPPORT/UTIs"

log() { echo -e "\033[0;34m[macOS]\033[0m $1"; }
success() { echo -e "\033[0;32m✓\033[0m $1"; }

setup() { mkdir -p "$BIN_DIR" "$LIB_DIR" "$ICONS_DIR" "$UTI_DIR"; }

install_core() {
    log "Installing agictl..."
    cp -r ../common/*.py "$LIB_DIR/"
    cat > "$BIN_DIR/agictl" << 'EOF'
#!/usr/bin/env python3
"""agictl — ARKHE OS Artifact CLI (macOS)"""
import sys, subprocess
from pathlib import Path
lib = Path(__file__).parent.parent / "lib" / "arkhe"
sys.path.insert(0, str(lib)) if lib.exists() else None
from verify import verify_artifact; from extract import extract_artifact

action, path = sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None
if action == "open" and verify_artifact(path):
    extract_artifact(path, f"{path}_extracted"); subprocess.run(["open", f"{path}_extracted"])
elif action == "verify": sys.exit(0 if verify_artifact(path) else 1)
elif action == "extract": extract_artifact(path, sys.argv[3] if len(sys.argv)>3 else f"{path}_extracted")
EOF
    chmod +x "$BIN_DIR/agictl"; success "agictl installed"
}

install_icons() {
    [[ "${SKIP_ICONS:-false}" == "true" ]] && return
    log "Creating .icns bundle..."
    mkdir -p "$ICONS_DIR/arkhe-icon.iconset"
    for size in 16 32 64 128 256 512 1024; do
        cp "../common/icons/arkhe-icon-${size}.png" \
           "$ICONS_DIR/arkhe-icon.iconset/icon_${size}x${size}.png" 2>/dev/null || true
    done
    command -v iconutil &>/dev/null && \
        iconutil -c icns -o "$ICONS_DIR/arkhe-icon.icns" "$ICONS_DIR/arkhe-icon.iconset"
    success "Icon bundle created"
}

register_uti() {
    log "Registering UTI..."
    cat > "$UTI_DIR/org.arkhe-os.agi.uti.plist" << 'EOF'
<?xml version="1.0"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>UTExportedTypeDeclarations</key><array><dict>
  <key>UTTypeIdentifier</key><string>org.arkhe-os.agi-artifact</string>
  <key>UTTypeDescription</key><string>ARKHE OS Artifact</string>
  <key>UTTypeConformsTo</key><array><string>public.data</string><string>public.archive</string></array>
  <key>UTTypeTagSpecification</key><dict>
    <key>public.filename-extension</key><array><string>agi</string></array>
    <key>public.mime-type</key><string>application/x-arkhe-agi</string></dict>
  <key>UTTypeIconFile</key><string>arkhe-icon.icns</string>
</dict></array></dict></plist>
EOF
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
        -f "$UTI_DIR/org.arkhe-os.agi.uti.plist" 2>/dev/null || true
    success "UTI registered: org.arkhe-os.agi-artifact"
}

create_finder_menu() {
    log "Creating Finder context menu..."
    mkdir -p "$HOME/Library/Services"
    # Simplified Automator service - in production use proper .workflow format
    mkdir -p "$HOME/Library/Services/Verify ARKHE Artifact.workflow/Contents"
    cat > "$HOME/Library/Services/Verify ARKHE Artifact.workflow/Contents/document.wflow" << EOF
<?xml version="1.0"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>actions</key><array><dict>
  <key>action</key><string>com.apple.RunShellScript</string>
  <key>parameters</key><dict><key>script</key>
  <string>for f in "\$@"; do $BIN_DIR/agictl verify "\$f"; done</string></dict>
</dict></array></dict></plist>
EOF
    success "Finder menu created"
}

update_path() {
    log "Updating PATH..."
    for p in "$HOME/.bash_profile" "$HOME/.zshrc"; do
        [[ -f "$p" ]] && ! grep -q "$BIN_DIR" "$p" 2>/dev/null && \
            echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$p"
    done
    success "PATH updated"
}

main() {
    log "🍎 Installing for macOS"
    setup; install_core; install_icons; register_uti; create_finder_menu; update_path
    echo ""; success "macOS install complete!"
    echo "  • Restart Finder: killall Finder"; echo "  • Test: agictl --help"
}
main "$@"
