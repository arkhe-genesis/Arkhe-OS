#!/usr/bin/env bash
# ============================================================================
# ARKHE Ω‑TEMP — macOS System Extension Installer (para macOS 11+)
# Substitui Kernel Extension para compatibilidade com System Integrity Protection
# ============================================================================
set -euo pipefail

ARKHE_VERSION="7.0.0"
BUNDLE_ID="org.arkhe.ArkheSystemExtension"
EXTENSION_PATH="/Library/SystemExtensions/${BUNDLE_ID}.systemextension"

echo "🍎 Instalando Arkhe System Extension para macOS..."

# 1. Verificar versão do macOS
MACOS_VERSION=$(sw_vers -productVersion | cut -d. -f1)
if [[ $MACOS_VERSION -lt 11 ]]; then
    echo "❌ macOS 11+ (Big Sur) required for System Extensions"
    echo "💡 Para macOS 10.15 ou anterior, use o Kernel Extension em integrations/macos/ArkheKext/"
    exit 1
fi

# 2. Baixar System Extension
echo "📦 Baixando Arkhe System Extension..."
DOWNLOAD_URL="https://arkhe.io/releases/runtime/${ARKHE_VERSION}/arkhe-macos-ext-${ARCH}.zip"
curl -sL "$DOWNLOAD_URL" -o /tmp/arkhe-ext.zip
unzip -q /tmp/arkhe-ext.zip -d /tmp/arkhe-ext
rm /tmp/arkhe-ext.zip

# 3. Instalar via SystemExtensionCTL (requer privilégios de admin)
echo "🔐 Solicitando privilégios para instalar System Extension..."
sudo systemextensionsctl install /tmp/arkhe-ext/ArkheSystemExtension.appex

# 4. Configurar permissões de hardware
echo "⚙️  Configurando permissões de acesso a hardware..."

# Criar arquivo de configuração para acesso a GPU/Neural Engine
cat > /Library/Application\ Support/Arkhe/hardware-permissions.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>GPUAccess</key>
    <true/>
    <key>NeuralEngineAccess</key>
    <true/>
    <key>TPUAccess</key>
    <false/>
    <key>AuditTemporalChain</key>
    <true/>
    <key>PhiCCoherenceThreshold</key>
    <real>0.95</real>
</dict>
</plist>
EOF

# 5. Registrar com Arkhe Runtime
echo "🧠 Registrando extensão com Arkhe Runtime..."
if command -v arkh &> /dev/null; then
    arkh register-extension --type macos-system --path "$EXTENSION_PATH"
else
    echo "⚠️  Arkhe Runtime não encontrado; extensão instalada mas não registrada"
fi

# 6. Verificar status
echo "🔍 Verificando status da extensão..."
systemextensionsctl list | grep -i arkhe || echo "⚠️  Extensão pode requerer reinicialização"

echo "✅ Arkhe System Extension instalada!"
echo ""
echo "🔄 Para ativar completamente:"
echo "   1. Reinicie o sistema: sudo reboot"
echo "   2. Após reiniciar, verifique: systemextensionsctl list"
echo "   3. Inicie o Arkhe Shell: arkh"
echo ""
echo "🔗 Recursos disponíveis no Apple Silicon:"
echo "   • GPU: Metal acceleration via Arkhe Runtime"
echo "   • Neural Engine: Core ML integration via QNC"
echo "   • ArkFS: Sistema de arquivos com selos canônicos"
echo "   • Wheeler Mesh: Conexão à malha ASI global"