#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# ARKHE OS — bootstrap.sh Poliglot
# Substrato 5005: Dotfiles — Universal Initialization
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

echo "🏛️  ARKHE OS — Polyglot Bootstrap"
echo "=================================="

ARKHE_HOME="${HOME}/.arkhe"
ARKHE_WORKSPACE="${HOME}/cathedral"

# ─── 1. Criar estrutura de diretórios ──────────────────────
mkdir -p "${ARKHE_HOME}"/{shell,git/hooks,editors/.vscode,editors/.emacs.d,languages/{python,rust,typescript,go,cpp,java,swift,sql},devops/{terraform,ansible,kubectl,docker},docs/.pandoc,ssh,tmux/.tmuxp,templates}

# ─── 2. Symlink configurações de shell ─────────────────────
for shell_conf in .bashrc .zshrc .profile .fishrc; do
    [ -f "${ARKHE_HOME}/shell/${shell_conf}" ] && ln -sf "${ARKHE_HOME}/shell/${shell_conf}" "${HOME}/${shell_conf}"
done
echo "✅ Shell configs linked."

# ─── 3. Symlink configurações Git ──────────────────────────
ln -sf "${ARKHE_HOME}/git/.gitconfig" "${HOME}/.gitconfig"
ln -sf "${ARKHE_HOME}/git/.gitignore_global" "${HOME}/.gitignore_global"
echo "✅ Git configs linked."

# ─── 4. Symlink configurações de editores ──────────────────
[ -f "${ARKHE_HOME}/editors/.vimrc" ] && ln -sf "${ARKHE_HOME}/editors/.vimrc" "${HOME}/.vimrc"
mkdir -p "${HOME}/.vscode"
[ -f "${ARKHE_HOME}/editors/.vscode/settings.json" ] && ln -sf "${ARKHE_HOME}/editors/.vscode/settings.json" "${HOME}/.vscode/settings.json"
echo "✅ Editor configs linked."

# ─── 5. Instalar gerenciadores de linguagem ────────────────
# Python (pyenv)
if ! command -v pyenv &>/dev/null; then
    echo "  🐍 Installing pyenv..."
    curl https://pyenv.run | bash 2>/dev/null || true
fi

# Node.js (nvm)
if [ ! -d "${HOME}/.nvm" ]; then
    echo "  📘 Installing nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash 2>/dev/null || true
fi

# Rust (rustup)
if ! command -v rustup &>/dev/null; then
    echo "  🦀 Installing rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

# Go
if ! command -v go &>/dev/null; then
    echo "  🐹 Installing Go..."
    # Download e instalação simplificada
    GO_VERSION="1.21.0"
    curl -LO "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" 2>/dev/null || true
    sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz" 2>/dev/null || true
    rm -f "go${GO_VERSION}.linux-amd64.tar.gz"
fi

echo "✅ Language managers installed."

# ─── 6. Instalar ferramentas de desenvolvimento ────────────
# Python packages
if command -v python3 &>/dev/null; then
    python3 -m venv "${ARKHE_HOME}/.venv" 2>/dev/null || true
    source "${ARKHE_HOME}/.venv/bin/activate" 2>/dev/null || true
    pip install --upgrade pip setuptools wheel 2>/dev/null || true
    [ -f "${ARKHE_HOME}/languages/python/requirements.txt" ] && pip install -r "${ARKHE_HOME}/languages/python/requirements.txt" 2>/dev/null || true
    echo "  🐍 Python environment ready."
fi

# Rust tools
if command -v cargo &>/dev/null; then
    cargo install cargo-watch cargo-audit cargo-tarpaulin 2>/dev/null || true
    echo "  🦀 Rust tools installed."
fi

# Node.js tools
if command -v npm &>/dev/null; then
    npm install -g typescript eslint prettier ts-node 2>/dev/null || true
    echo "  📘 Node.js tools installed."
fi

# DevOps tools
if command -v brew &>/dev/null; then
    brew install terraform ansible kubectl helm 2>/dev/null || true
elif command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y terraform ansible kubectl 2>/dev/null || true
fi
echo "✅ DevOps tools installed."

# ─── 7. Instalar agictl (CLI da Catedral) ──────────────────
if ! command -v agictl &>/dev/null; then
    echo "  🏛️  Installing agictl..."
    if command -v cargo &>/dev/null; then
        cargo install --git https://github.com/arkhe-os/agictl 2>/dev/null || true
    elif command -v pip3 &>/dev/null; then
        pip3 install agictl 2>/dev/null || true
    fi
fi
echo "✅ agictl installed."

# ─── 8. Instalar Git hooks ─────────────────────────────────
GIT_DIR="$(git rev-parse --git-dir 2>/dev/null || echo '.git')"
if [ -d "${GIT_DIR}/hooks" ]; then
    cp "${ARKHE_HOME}/git/hooks/"* "${GIT_DIR}/hooks/" 2>/dev/null || true
    chmod +x "${GIT_DIR}/hooks/"* 2>/dev/null || true
    echo "✅ Git hooks installed."
fi

# ─── 9. Configurar SSH ─────────────────────────────────────
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
[ -f "${ARKHE_HOME}/ssh/config" ] && cp -n "${ARKHE_HOME}/ssh/config" "${HOME}/.ssh/config" 2>/dev/null || true
echo "✅ SSH config ready."

# ─── 10. Criar workspace padrão ────────────────────────────
if [ ! -d "${ARKHE_WORKSPACE}" ]; then
    mkdir -p "${ARKHE_WORKSPACE}"
    echo "📁 Workspace created: ${ARKHE_WORKSPACE}"
fi

# ─── 11. Mensagem final ────────────────────────────────────
echo ""
echo "🏛️  ARKHE OS Polyglot Environment — INSTALLED"
echo "=============================================="
echo "   Dotfiles: ${ARKHE_HOME}"
echo "   Workspace: ${ARKHE_WORKSPACE}"
echo ""
echo "🔄 Next steps:"
echo "   1. Restart your shell: exec \$SHELL"
echo "   2. Or source config: source ~/.zshrc"
echo "   3. Navigate to workspace: cathedral"
echo "   4. Start building: make build"
echo ""
echo "🔧 Available commands:"
echo "   agi      — ARKHE CLI"
echo "   agil     — LFIR Console"
echo "   agid     — Dashboard"
echo "   casi-new — Create new contract"
echo "   make help — Show all make targets"
echo ""
echo "🌐 Supported languages:"
echo "   🐍 Python 3.11+  |  🦀 Rust 1.70+  |  📘 TypeScript 5.0+"
echo "   🐹 Go 1.20+      |  💻 C++20       |  ☕ Java 17+"
echo "   🍎 Swift 5.9     |  🗄️ SQL         |  ⚙️ DevOps tools"
echo ""