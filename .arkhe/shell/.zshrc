#!/usr/bin/env zsh
# ═══════════════════════════════════════════════════════════════
# ARKHE OS — .zshrc Poliglot para Desenvolvedores Soberanos
# Substrato 5005: Dotfiles — Polyglot Shell Configuration
# ═══════════════════════════════════════════════════════════════

# ─── Identidade & Ambiente ───────────────────────────────────
export ARKHE_DEVELOPER="${USER}"
export ARKHE_HOME="${HOME}/.arkhe"
export ARKHE_WORKSPACE="${HOME}/cathedral"
export ARKHE_LANG="${ARKHE_LANG:-python}"  # Default language context

# ─── Path Universal ─────────────────────────────────────────
export PATH="${ARKHE_HOME}/bin:${PATH}"
export PATH="${ARKHE_WORKSPACE}/target/release:${PATH}"  # Rust
export PATH="${HOME}/.local/bin:${PATH}"                  # Python user scripts
export PATH="${HOME}/.cargo/bin:${PATH}"                  # Rust toolchain
export PATH="${HOME}/.npm-global/bin:${PATH}"             # Node.js global
export PATH="${HOME}/go/bin:${PATH}"                      # Go binaries
export PATH="${HOME}/.dotnet/tools:${PATH}"               # .NET tools

# ─── Language Managers ─────────────────────────────────────
# Python (pyenv)
export PYENV_ROOT="${HOME}/.pyenv"
export PATH="${PYENV_ROOT}/bin:${PATH}"
if command -v pyenv &>/dev/null; then
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
fi

# Node.js (nvm)
export NVM_DIR="${HOME}/.nvm"
[ -s "${NVM_DIR}/nvm.sh" ] && source "${NVM_DIR}/nvm.sh"
[ -s "${NVM_DIR}/bash_completion" ] && source "${NVM_DIR}/bash_completion"

# Rust (rustup)
[ -f "${HOME}/.cargo/env" ] && source "${HOME}/.cargo/env"

# Go
export GOPATH="${HOME}/go"
export PATH="${GOPATH}/bin:${PATH}"

# Java (jenv)
export JENV_ROOT="${HOME}/.jenv"
export PATH="${JENV_ROOT}/bin:${PATH}"
if command -v jenv &>/dev/null; then
    eval "$(jenv init -)"
fi

# ─── Prompt ARKHE Poliglot ──────────────────────────────────
autoload -U colors && colors

# Função para exibir linguagem atual
_arkhe_lang_prompt() {
    if [ -f "pyproject.toml" ]; then echo "🐍"
    elif [ -f "Cargo.toml" ]; then echo "🦀"
    elif [ -f "package.json" ]; then echo "📘"
    elif [ -f "go.mod" ]; then echo "🐹"
    elif [ -f "*.cpp" -o -f "*.h" ]; then echo "💻"
    elif [ -f "*.java" ]; then echo "☕"
    elif [ -f "*.swift" ]; then echo "🍎"
    else echo "🔧"
    fi
}

PROMPT='%{$fg[yellow]%}🏛️ %{$fg[cyan]%}%2~%{$reset_color%} %{$fg[blue]%}$(_arkhe_lang_prompt)%{$reset_color%} %{$fg[green]%}❯%{$reset_color%} '
RPROMPT='%{$fg[magenta]%}[Φ:$(agictl query --type coherence --format text 2>/dev/null || echo "?")]%{$reset_color%}'

# ─── Aliases Canônicos Poliglot ─────────────────────────────
# ARKHE Core
alias cathedral="cd ${ARKHE_WORKSPACE}"
alias agi="agictl"
alias agil="agictl lfir"
alias agid="agictl dashboard"
alias agig="agictl genesis"
alias agiv="agictl verify"
alias agip="agictl pack"

# Python
alias py="python3"
alias pip="pip3"
alias pytest="python3 -m pytest"
alias black="black --config ${ARKHE_HOME}/languages/python/.pyproject.toml"
alias pylint="pylint --rcfile=${ARKHE_HOME}/languages/python/.pylintrc"
alias mypy="mypy --config-file=${ARKHE_HOME}/languages/python/.mypy.ini"

# Rust
alias cargo="cargo --config ${ARKHE_HOME}/languages/rust/.cargo/config.toml"
alias rustfmt="rustfmt --config-path ${ARKHE_HOME}/languages/rust/.rustfmt.toml"
alias clippy="cargo clippy -- -D warnings"

# TypeScript/Node
alias npm="npm --prefix ${ARKHE_WORKSPACE}"
alias npx="npx --prefer-local"
alias tsc="tsc --project ${ARKHE_HOME}/languages/typescript/tsconfig.base.json"
alias eslint="eslint -c ${ARKHE_HOME}/languages/typescript/.eslintrc.json"
alias prettier="prettier --config ${ARKHE_HOME}/languages/typescript/.prettierrc"

# Go
alias gofmt="gofmt -s -w"
alias golangci="golangci-lint run -c ${ARKHE_HOME}/languages/go/.golangci.yml"

# C++
alias clang-format="clang-format -i --style=file:${ARKHE_HOME}/languages/cpp/.clang-format"
alias clang-tidy="clang-tidy -p build -config-file=${ARKHE_HOME}/languages/cpp/.clang-tidy"

# Java
alias gradle="gradle --init-script ${ARKHE_HOME}/languages/java/init.gradle"
alias checkstyle="checkstyle -c ${ARKHE_HOME}/languages/java/checkstyle.xml"

# Swift
alias swiftlint="swiftlint --config ${ARKHE_HOME}/languages/swift/.swiftlint.yml"

# DevOps
alias tf="terraform"
alias k="kubectl"
alias ka="kubectl apply -f"
alias kg="kubectl get"
alias kd="kubectl describe"
alias kl="kubectl logs -f"

# ─── Funções Canônicas ──────────────────────────────────────
# Criar novo contrato .casi
function casi-new() {
    local name="${1:?Usage: casi-new <contract_name>}"
    local lang="${2:-python}"
    cp "${ARKHE_HOME}/templates/substrate.${lang}" "${name}.${lang}"
    echo "📜 Substrate ${name}.${lang} created"
}

# Testar integridade multi-linguagem
function arkhe-test() {
    echo "🧪 Running polyglot tests..."

    # Python
    if [ -f "pyproject.toml" ]; then
        echo "  🐍 Python tests..."
        pytest --quiet
    fi

    # Rust
    if [ -f "Cargo.toml" ]; then
        echo "  🦀 Rust tests..."
        cargo test --quiet
    fi

    # TypeScript
    if [ -f "package.json" ]; then
        echo "  📘 TypeScript tests..."
        npm test -- --passWithNoTests
    fi

    # Go
    if [ -f "go.mod" ]; then
        echo "  🐹 Go tests..."
        go test ./...
    fi

    echo "✅ Polyglot tests complete"
}

# Build multi-linguagem
function arkhe-build() {
    echo "⚙️  Building polyglot project..."

    # Rust (se presente)
    if [ -f "Cargo.toml" ]; then
        cargo build --release
    fi

    # Python (se presente)
    if [ -f "pyproject.toml" ]; then
        python -m build
    fi

    # TypeScript (se presente)
    if [ -f "tsconfig.json" ]; then
        tsc --build
    fi

    echo "✅ Build complete"
}

# ─── Completions ────────────────────────────────────────────
# ARKHE CLI completions
if command -v agictl &>/dev/null; then
    eval "$(agictl completion zsh 2>/dev/null || true)"
fi

# Language-specific completions
if command -v poetry &>/dev/null; then
    eval "$(poetry completions zsh)"
fi
if command -v rustup &>/dev/null; then
    source <(rustup completions zsh cargo)
fi
if command -v kubectl &>/dev/null; then
    source <(kubectl completion zsh)
fi

# ─── Bem-vindo Poliglot ─────────────────────────────────────
if [ -z "${ARKHE_SILENT}" ]; then
    echo "🏛️  ARKHE OS — Polyglot Developer Environment"
    echo "   $(agictl --version 2>/dev/null || echo 'agictl: not installed')"
    echo "   Lang: $(_arkhe_lang_prompt) ${ARKHE_LANG}"
    echo "   Φ_C: $(agictl query --type coherence --format text 2>/dev/null || echo 'offline')"
    echo ""
fi