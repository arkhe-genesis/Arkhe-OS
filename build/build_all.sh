#!/bin/bash
set -euo pipefail
echo "🏛️ ARKHE OS — Complete Build"
echo "============================"

# 1. Rust toolchain & WiX/Inno
rustup target add x86_64-pc-windows-msvc
sudo apt-get install -y wixl innoextract  # or chocolatey on Windows

# 2. Build workspace
cargo build --workspace --release

# 3. Test
cargo test --workspace --features full

# 4. Package components
python3 scripts/collect_python.py
bash scripts/fetch_models.sh

# 5. Build MSI (WiX)
cd build/windows/wix
candle ARKHE.wxs -ext WixUtilExtension
light ARKHE.wixobj -ext WixUtilExtension -out ../../output/ARKHE.msi

# 6. Build EXE (Inno)
cd ../inno
iscc ARKHE.iss

# 7. Create self-extracting PowerShell
cd ../powershell
zip -r ../../output/arkhe-package.zip ../../output/bin ../../share
echo "Arkhe-Bootstrap.ps1 and arkhe-package.zip ready."

echo "🎉 Done. Artifacts in build/output/:"
ls -lh build/output/