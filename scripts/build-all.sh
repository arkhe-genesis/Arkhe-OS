#!/bin/bash

# ARKHE OS Multi-Platform Build Script

echo "🏗️  Building Arkhe OS for all platforms..."

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "Node.js required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required"; exit 1; }
command -v cargo >/dev/null 2>&1 || { echo "Rust/Cargo required"; exit 1; }

# Build desktop (Tauri)
echo "🖥️  Building desktop version..."
cd ui/desktop
npm install
npm run build
npm run tauri build
cd ../..

# Build mobile (Capacitor)
echo "📱 Building mobile version..."
cd ui/mobile
npm install
npm run build

# Android
echo "🤖 Building Android..."
npx cap add android
npx cap sync android
npx cap build android

# iOS (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Building iOS..."
    npx cap add ios
    npx cap sync ios
    npx cap build ios
fi

cd ../..

echo "📦 Creating distribution packages..."
mkdir -p dist

# Copy build artifacts
cp ui/desktop/src-tauri/target/release/bundle/*/*.msi dist/ 2>/dev/null || true
cp ui/desktop/src-tauri/target/release/bundle/*/*.dmg dist/ 2>/dev/null || true
cp ui/desktop/src-tauri/target/release/bundle/*/*.deb dist/ 2>/dev/null || true
cp ui/mobile/android/app/build/outputs/apk/release/*.apk dist/ 2>/dev/null || true
cp ui/mobile/ios/App/App.ipa dist/ 2>/dev/null || true

echo "✅ Build complete! Artifacts in dist/"
ls -la dist/