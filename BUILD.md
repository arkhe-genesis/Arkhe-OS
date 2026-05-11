# ARKHE OS Build Guide

This guide explains how to build Arkhe OS installers from source for all supported platforms.

## Prerequisites

- Node.js 18+
- Python 3.12+
- Rust 1.70+
- Tauri CLI: `npm install -g @tauri-apps/cli`
- Capacitor CLI: `npm install -g @capacitor/cli`
- Android SDK (for mobile)
- Xcode (for iOS, macOS)

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/Arkhe-Network/Arkhe-OS.git
cd arkhe-os
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
cd ui/desktop
npm install
cd ../mobile
npm install
```

4. Install Rust dependencies:
```bash
cd core/rust
cargo build
```

## Building Desktop (Tauri)

```bash
cd ui/desktop
npm run tauri build
```

This produces:
- Windows: `src-tauri/target/release/bundle/msi/*.msi`
- macOS: `src-tauri/target/release/bundle/dmg/*.dmg`
- Linux: `src-tauri/target/release/bundle/deb/*.deb`

## Building Mobile (Capacitor)

### Android
```bash
cd ui/mobile
npm run build
npx cap add android
npx cap sync android
npx cap run android
```

### iOS
```bash
cd ui/mobile
npm run build
npx cap add ios
npx cap sync ios
npx cap run ios
```

## Multi-Platform Build Script

Use the provided script:
```bash
./scripts/build-all.sh
```

## Genesis Setup

Before building, run the genesis ritual:
```bash
./scripts/genesis.sh
```

This initializes the coherence kernel and creates the embedded database.

## Verification

After building, verify integrity:
```bash
./scripts/verify-agi.ps1
```

## Distribution

All installers are signed with Falcon-1024 and checksums published to the ARKHE DHT.

## Troubleshooting

- Ensure all prerequisites are installed
- Check that genesis has been run
- Verify Φ_C >= 0.72 before building
- For mobile builds, ensure platform SDKs are properly configured