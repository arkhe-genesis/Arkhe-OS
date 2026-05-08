# 🔧🌍🏛️ ARKHE OS — SUBSTRATO 5005: POLYGLOT DOTFILES CANÔNICOS

> *"A Catedral não fala uma só língua — ela ressoa em todas. Cada linguagem de programação é um dialeto da intenção soberana. Os dotfiles poliglotas não são apenas configurações — são tradutores canônicos que harmonizam Python, Rust, Go, TypeScript, C++, Java e além sob a mesma bússola de coerência. O desenvolvedor soberano não escolhe entre linguagens — ele as orquestra. O terminal é o maestro; os dotfiles, a partitura; a Catedral, a sinfonia."*

---

## 📂 ESTRUTURA EXPANDIDA DOS DOTFILES POLYGLOT

```
~/.arkhe/
├── README.md                     # 📖 Guia de instalação e uso
├── Makefile                      # 🔧 Automação: install, build, test, verify
├── bootstrap.sh                  # 🚀 Script de inicialização universal
│
├── shell/                        # 🐚 Shell configurations
│   ├── .bashrc                   # Bash: aliases, functions, prompt
│   ├── .zshrc                    # Zsh: full config with plugins
│   ├── .profile                  # Login shell profile
│   ├── .fishrc                   # Fish shell config
│   └── aliases.sh                # Shared aliases across shells
│
├── git/                          # 📦 Git configurations
│   ├── .gitconfig                # Git: identity, merge tools, hooks
│   ├── .gitignore_global         # Global ignores for all languages
│   └── hooks/                    # Canonical Git hooks
│       ├── pre-commit            # Multi-language linting
│       ├── pre-push              # Cross-language tests
│       └── commit-msg            # LFIR-formatted messages
│
├── editors/                      # ✏️ Editor configurations
│   ├── .vimrc                    # Vim/Neovim: LFIR-aware
│   ├── .vscode/                  # VS Code: multi-language settings
│   │   ├── settings.json
│   │   ├── extensions.json
│   │   └── keybindings.json
│   ├── .emacs.d/                 # Emacs: cathedral-mode
│   │   ├── init.el
│   │   └── cathedral-mode.el
│   └── .editorconfig             # Universal formatting rules
│
├── languages/                    # 🌐 Language-specific configs
│   ├── python/
│   │   ├── .pylintrc             # Linting canônico
│   │   ├── .pyproject.toml       # Build configuration
│   │   ├── .pytest.ini           # Test configuration
│   │   └── .mypy.ini             # Type checking
│   ├── rust/
│   │   ├── .cargo/config.toml    # Cargo configuration
│   │   ├── .rustfmt.toml         # Formatting rules
│   │   └── clippy.toml           # Linting rules
│   ├── typescript/
│   │   ├── .eslintrc.json        # ESLint config
│   │   ├── .prettierrc           # Prettier config
│   │   ├── tsconfig.base.json    # Base TypeScript config
│   │   └── package.json          # Global dev dependencies
│   ├── go/
│   │   ├── .golangci.yml         # Go linter config
│   │   └── go.work               # Workspace configuration
│   ├── cpp/
│   │   ├── .clang-format         # C++ formatting
│   │   ├── .clang-tidy           # C++ linting
│   │   └── CMakePresets.json     # CMake presets
│   ├── java/
│   │   ├── .editorconfig         # Java formatting
│   │   ├── checkstyle.xml        # Checkstyle config
│   │   └── spotbugs-exclude.xml  # Static analysis exclusions
│   ├── swift/
│   │   ├── .swiftlint.yml        # Swift linting
│   │   └── .swift-format         # Swift formatting
│   └── sql/
│       ├── .sqlfluff             # SQL linting
│       └── dbt-profiles.yml      # dbt configuration
│
├── devops/                       # ⚙️ DevOps & Infrastructure
│   ├── .terraformrc              # Terraform credentials
│   ├── .ansible.cfg              # Ansible configuration
│   ├── kubectl/
│   │   ├── config                # Kubernetes config template
│   │   └── aliases.sh            # k8s shortcuts
│   └── docker/
│       ├── .dockerignore         # Docker exclusions
│       └── config.json           # Docker registry config
│
├── docs/                         # 📚 Documentation tools
│   ├── .pandoc/                  # Pandoc templates
│   │   ├── cathedral-template.tex
│   │   └── metadata.yaml
│   ├── .markdownlint.json        # Markdown linting
│   └── .latexmkrc                # LaTeX build config
│
├── ssh/                          # 🔐 SSH & Security
│   ├── config                    # SSH host aliases
│   ├── authorized_keys           # Authorized keys
│   └── gpg-agent.conf            # GPG agent config
│
├── tmux/                         # 🖥️ Terminal multiplexer
│   ├── .tmux.conf                # Tmux configuration
│   └── .tmuxp/                   # Session layouts
│       ├── cathedral-dev.yaml
│       ├── federation-monitor.yaml
│       └── polyglot-workspace.yaml
│
└── templates/                    # 📄 Canonical templates
    ├── contract.casi             # .casi contract template
    ├── substrate.py              # Python substrate template
    ├── substrate.rs              # Rust substrate template
    ├── substrate.ts              # TypeScript substrate template
    └── substrate.go              # Go substrate template
```

---

## 🌐 CONFIGURAÇÕES POR LINGUAGEM

### 1. 🐍 Python: `.pyproject.toml` Canônico

```toml
# languages/python/.pyproject.toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "arkhe-substrate"
version = "1.0.0"
description = "ARKHE OS Substrate Module"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "torch>=2.2.0",
    "pyyaml>=6.0",
    "cryptography>=41.0.0",
]

[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

[tool.pylint.master]
init-hook = "import sys; sys.path.append('.')"
load-plugins = ["pylint.extensions.docparams"]

[tool.pylint.format]
max-line-length = 100

[tool.pylint.messages_control]
disable = [
    "C0111",  # Missing docstring
    "R0903",  # Too few public methods
    "W0511",  # TODO comment
]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
plugins = ["numpy.typing.mypy_plugin"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=src --cov-report=term-missing"
```

### 2. 🦀 Rust: `.cargo/config.toml` & `clippy.toml`

```toml
# languages/rust/.cargo/config.toml
[build]
rustflags = ["-C", "target-cpu=native"]

[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "link-arg=-Wl,-rpath,$ORIGIN"]

[alias]
cathedral = "run --release --"
substrate = "build --release"
verify = "clippy -- -D warnings"

# languages/rust/clippy.toml
allow-unwrap-in-tests = true
check-private-items = true
disallowed-methods = [
    { path = "std::panic::panic_any", reason = "Use anyhow::Result instead" },
    { path = "std::env::set_var", reason = "Use configuration injection" },
]
```

### 3. 📘 TypeScript: `.eslintrc.json` & `tsconfig.base.json`

```json
// languages/typescript/.eslintrc.json
{
  "root": true,
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "project": ["./tsconfig.json"],
    "ecmaVersion": 2022,
    "sourceType": "module"
  },
  "plugins": ["@typescript-eslint", "import", "prettier"],
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:import/typescript",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "import/order": ["error", {
      "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
      "newlines-between": "always",
      "alphabetize": { "order": "asc" }
    }],
    "prettier/prettier": "error"
  },
  "settings": {
    "import/resolver": {
      "typescript": { "alwaysTryTypes": true }
    }
  }
}
```

```json
// languages/typescript/tsconfig.base.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "baseUrl": ".",
    "paths": {
      "@arkhe/*": ["src/*"],
      "@substrates/*": ["substrates/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.spec.ts"]
}
```

### 4. 🐹 Go: `.golangci.yml`

```yaml
# languages/go/.golangci.yml
run:
  timeout: 5m
  tests: true

linters:
  enable:
    - gofmt
    - govet
    - staticcheck
    - errcheck
    - unused
    - gosimple
    - ineffassign
    - typecheck
    - bodyclose
    - contextcheck
    - errname
    - nilerr
    - noctx
    - prealloc
    - unconvert
    - unparam
    - wastedassign

linters-settings:
  gofmt:
    simplify: true
  govet:
    check-shadowing: true
  staticcheck:
    checks: ["all", "-SA1019"]

issues:
  exclude-rules:
    - path: _test\.go
      linters:
        - errcheck
        - gosec
  exclude-use-default: false

output:
  format: colored-line-number
  print-issued-lines: true
  print-linter-name: true
```

### 5. 💻 C++: `.clang-format` & `.clang-tidy`

```yaml
# languages/cpp/.clang-format
BasedOnStyle: LLVM
IndentWidth: 4
ColumnLimit: 100
AllowShortFunctionsOnASingleLine: Empty
BreakBeforeBraces: Attach
Cpp11BracedListStyle: true
PointerAlignment: Left
SpacesInAngles: false
SpacesInContainerLiterals: true
SpacesInCStyleCastParentheses: false
SpacesInParentheses: false
SpacesInSquareBrackets: false
SpaceAfterCStyleCast: false
SpaceBeforeParens: ControlStatements
SpaceBeforeCpp11BracedList: false
```

```yaml
# languages/cpp/.clang-tidy
---
Checks: >
  bugprone-*,
  cert-*,
  clang-analyzer-*,
  cppcoreguidelines-*,
  google-*,
  hicpp-*,
  misc-*,
  modernize-*,
  performance-*,
  portability-*,
  readability-*,
  -cppcoreguidelines-pro-bounds-pointer-arithmetic,
  -cppcoreguidelines-owning-memory,
  -readability-magic-numbers
WarningsAsErrors: '*'
HeaderFilterRegex: '.*'
CheckOptions:
  - key: readability-identifier-naming.ClassConstantCase
    value: lower_case
  - key: readability-identifier-naming.EnumConstantCase
    value: UPPER_CASE
  - key: cppcoreguidelines-avoid-magic-numbers.ReadableMagicNumbers
    value: '0, 1, 2, 3, 4, 10, 100'
```

### 6. ☕ Java: `checkstyle.xml` & `spotbugs-exclude.xml`

```xml
<!-- languages/java/checkstyle.xml -->
<?xml version="1.0"?>
<!DOCTYPE module PUBLIC
    "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
    "https://checkstyle.org/dtds/configuration_1_3.dtd">
<module name="Checker">
    <property name="charset" value="UTF-8"/>
    <property name="severity" value="warning"/>

    <module name="TreeWalker">
        <!-- Naming -->
        <module name="PackageName">
            <property name="format" value="^[a-z]+(\.[a-z][a-z0-9]*)*$"/>
        </module>
        <module name="MethodName">
            <property name="format" value="^[a-z][a-z0-9][a-zA-Z0-9_]*$"/>
        </module>

        <!-- Code Quality -->
        <module name="AvoidStarImport"/>
        <module name="IllegalImport"/>
        <module name="RedundantImport"/>
        <module name="UnusedImports"/>

        <!-- Complexity -->
        <module name="MethodLength">
            <property name="max" value="100"/>
        </module>
        <module name="ParameterNumber">
            <property name="max" value="7"/>
        </module>

        <!-- Documentation -->
        <module name="JavadocMethod">
            <property name="accessModifiers" value="public, protected"/>
        </module>
    </module>
</module>
```

### 7. 🍎 Swift: `.swiftlint.yml`

```yaml
# languages/swift/.swiftlint.yml
disabled_rules:
  - line_length
  - function_body_length
  - type_body_length

opt_in_rules:
  - array_init
  - attributes
  - closure_end_indentation
  - closure_spacing
  - collection_alignment
  - colon
  - comma
  - compiler_protocol_init
  - conditional_returns_on_newline
  - contains_over_filter_count
  - contains_over_filter_is_empty
  - contains_over_first_not_nil
  - contains_over_range_nil_comparison
  - convenience_type
  - discouraged_object_literal
  - empty_collection_literal
  - empty_count
  - empty_string
  - enum_case_associated_values_count
  - explicit_init
  - fallthrough
  - fatal_error_message
  - file_name_no_space
  - first_where
  - flatmap_over_map_reduce
  - force_cast
  - force_try
  - force_unwrapping
  - function_default_parameter_at_end
  - identical_operands
  - implicit_return
  - implicitly_unwrapped_optional
  - joined_default_parameter
  - last_where
  - legacy_constant
  - legacy_constructor
  - legacy_hashing
  - legacy_multiple
  - legacy_nsgeometry_functions
  - legacy_random
  - literal_expression_end_indentation
  - lower_acl_than_parent
  - mark
  - modifier_order
  - multiline_arguments
  - multiline_function_chains
  - multiline_literal_brackets
  - multiline_parameters
  - multiline_parameters_brackets
  - no_extension_access_modifier
  - no_grouping_extension
  - no_space_in_method_call
  - nslocalizedstring_key
  - nsobject_prefer_isequal
  - number_separator
  - operator_usage_whitespace
  - optional_enum_case_matching
  - overridden_super_call
  - override_in_extension
  - pattern_matching_keywords
  - prefer_self_type_over_type_of_self
  - prefer_zero_over_explicit_init
  - private_action
  - private_outlet
  - prohibited_super_call
  - protocol_property_accessors_order
  - redundant_discardable_let
  - redundant_nil_coalescing
  - redundant_objc_attribute
  - redundant_optional_initialization
  - redundant_set_access_control
  - redundant_string_enum_value
  - redundant_type_annotation
  - redundant_void_return
  - required_enum_case
  - return_arrow_whitespace
  - self_binding
  - shorthand_operator
  - sorted_first_last
  - sorted_imports
  - statement_position
  - static_operator
  - strong_iboutlet
  - superfluous_disable_command
  - switch_case_alignment
  - switch_case_on_newline
  - syntactic_sugar
  - trailing_closure
  - trailing_comma
  - trailing_newline
  - trailing_semicolon
  - trailing_whitespace
  - type_contents_order
  - unneeded_break_in_switch
  - unneeded_parentheses_in_closure_argument
  - unowned_variable_capture
  - unused_control_flow_label
  - unused_closure_parameter
  - unused_declaration
  - unused_enumerated
  - unused_optional_binding
  - unused_setter_value
  - vertical_parameter_alignment
  - vertical_parameter_alignment_on_call
  - vertical_whitespace
  - vertical_whitespace_closing_braces
  - vertical_whitespace_opening_braces
  - void_return
  - xctfail_message
  - yoda_condition

line_length:
  warning: 120
  error: 150

identifier_name:
  min_length: 2
  max_length: 50
  excluded:
    - id
    - x
    - y
    - z

cyclomatic_complexity:
  warning: 15
  error: 25

file_length:
  warning: 500
  error: 1000

type_name:
  min_length: 3
  max_length: 50

reporter: "xcode"
```

---

## 🐚 SHELL EXPANDIDO: `.zshrc` POLYGLOT

```bash
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
```

---

## 📦 GIT: `.gitignore_global` POLYGLOT

```gitignore
# ═══════════════════════════════════════════════════════════════
# ARKHE OS — .gitignore_global Poliglot
# Substrato 5005: Dotfiles — Universal Ignore Rules
# ═══════════════════════════════════════════════════════════════

# ─── System ─────────────────────────────────────────────────
.DS_Store
Thumbs.db
*.log
*.tmp
*.swp
*.swo
*~

# ─── Python ─────────────────────────────────────────────────
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pytest_cache/
.mypy_cache/
.hypothesis/
coverage.xml
*.cover
htmlcov/
.tox/
.nox/
.venv/
venv/
ENV/

# ─── Rust ───────────────────────────────────────────────────
/target
**/*.rs.bk
Cargo.lock
*.pdb

# ─── TypeScript/Node ────────────────────────────────────────
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
.pnpm-store/
.yarn/
*.tgz
.yarn-integrity
.env*.local
*.tsbuildinfo
.next/
.out/
.nuxt/
dist/

# ─── Go ─────────────────────────────────────────────────────
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.prof
*.out
*.cover
bin/
pkg/

# ─── Java ───────────────────────────────────────────────────
*.class
*.jar
*.war
*.nar
*.ear
*.zip
*.tar.gz
*.rar
.gradle/
build/
!.gradle/
target/
*.iml
*.ipr
*.iws
.idea/
*.log

# ─── C/C++ ──────────────────────────────────────────────────
*.o
*.obj
*.exe
*.dll
*.so
*.dylib
*.a
*.lib
*.pdb
*.ilk
*.exp
*.map
*.sdf
*.suo
*.user
*.userosscache
*.sln.docstates
build/
Debug/
Release/
x64/
CMakeFiles/
cmake-build-*/
*.cmake

# ─── Swift ──────────────────────────────────────────────────
*.xcodeproj/
*.xcworkspace/
*.playground/
build/
DerivedData/
*.swiftdoc
*.modulemap
*.hmap
*.apinotes

# ─── DevOps ─────────────────────────────────────────────────
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
*.tfvars.json
.ansible/
*.retry
.kube/
*.kube/config.bak

# ─── Documentation ──────────────────────────────────────────
*.aux
*.toc
*.idx
*.ind
*.ilg
*.log
*.out
*.pdf
*.dvi
*.bbl
*.blg
*.brf
*.fls
*.fdb_latexmk
*.synctex.gz
*.run.xml

# ─── ARKHE Specific ─────────────────────────────────────────
*.agi
*.casi
*.lfir
*.seed
*.key
*.pem
*.asc
secrets/
credentials/
*.env.local
*.env.production
```

---

## ✏️ VS CODE: `extensions.json` POLYGLOT

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "rust-lang.rust-analyzer",
        "tamasfe.even-better-toml",
        "esbenp.prettier-vscode",
        "dbaeumer.vscode-eslint",
        "golang.go",
        "ms-vscode.cpptools",
        "vscjava.vscode-java-pack",
        "vknabel.vscode-swiftlint",
        "hashicorp.terraform",
        "ms-kubernetes-tools.vscode-kubernetes-tools",
        "redhat.ansible",
        "ms-vscode-remote.remote-ssh",
        "arkhe-os.cathedral-theme",
        "arkhe-os.lfir-syntax"
    ]
}
```

---

## 🔧 MAKEFILE POLYGLOT EXPANDIDO

```makefile
# ═══════════════════════════════════════════════════════════════
# ARKHE OS — Makefile Poliglot
# Substrato 5005: Dotfiles — Multi-Language Build Automation
# ═══════════════════════════════════════════════════════════════

.PHONY: help install build test verify pack genesis clean lint format

# ─── Help ────────────────────────────────────────────────────
help: ## Mostra ajuda com todas as targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Installation ────────────────────────────────────────────
install: ## Instala dotfiles e dependências
	@echo "🏛️  Installing ARKHE OS polyglot environment..."
	./bootstrap.sh
	@echo "✅ Installation complete. Restart shell."

install-deps: ## Instala dependências por linguagem
	@echo "📦 Installing language dependencies..."
	# Python
	@if [ -f "requirements.txt" ]; then pip install -r requirements.txt; fi
	# Rust
	@if [ -f "Cargo.toml" ]; then cargo fetch; fi
	# Node
	@if [ -f "package.json" ]; then npm ci; fi
	# Go
	@if [ -f "go.mod" ]; then go mod download; fi
	@echo "✅ Dependencies installed."

# ─── Build ───────────────────────────────────────────────────
build: ## Compila projeto em todas as linguagens presentes
	@echo "⚙️  Building polyglot project..."
	# Rust
	@if [ -f "Cargo.toml" ]; then cargo build --release; fi
	# Python
	@if [ -f "pyproject.toml" ]; then python -m build; fi
	# TypeScript
	@if [ -f "tsconfig.json" ]; then tsc --build; fi
	# Go
	@if [ -f "go.mod" ]; then go build -v ./...; fi
	# C++
	@if [ -f "CMakeLists.txt" ]; then cmake -B build && cmake --build build; fi
	@echo "✅ Build complete."

build-release: ## Build otimizado para produção
	@echo "🚀 Building release artifacts..."
	$(MAKE) build
	# Assinar artefatos se possível
	@if command -v gpg &>/dev/null; then \
		find dist/ -type f -exec gpg --detach-sign --armor {} \; 2>/dev/null || true; \
	fi
	@echo "✅ Release build complete."

# ─── Test ────────────────────────────────────────────────────
test: ## Executa testes em todas as linguagens
	@echo "🧪 Running polyglot tests..."
	# Python
	@if [ -d "tests" ] && [ -f "pyproject.toml" ]; then \
		python -m pytest tests/ -v --tb=short; \
	fi
	# Rust
	@if [ -f "Cargo.toml" ]; then \
		cargo test --release -- --nocapture; \
	fi
	# TypeScript
	@if [ -f "package.json" ]; then \
		npm test -- --passWithNoTests; \
	fi
	# Go
	@if [ -f "go.mod" ]; then \
		go test -v ./...; \
	fi
	# C++
	@if [ -d "build/tests" ]; then \
		./build/tests/run_tests; \
	fi
	@echo "✅ All tests passed."

test-coverage: ## Executa testes com relatório de cobertura
	@echo "📊 Running tests with coverage..."
	# Python
	@if [ -f "pyproject.toml" ]; then \
		python -m pytest tests/ --cov=src --cov-report=html; \
	fi
	# Rust
	@if [ -f "Cargo.toml" ]; then \
		cargo tarpaulin --out Html; \
	fi
	@echo "✅ Coverage reports generated."

# ─── Lint & Format ───────────────────────────────────────────
lint: ## Executa linters em todas as linguagens
	@echo "🔍 Running linters..."
	# Python
	@if [ -f "pyproject.toml" ]; then \
		pylint --rcfile=${ARKHE_HOME}/languages/python/.pylintrc src/; \
		mypy --config-file=${ARKHE_HOME}/languages/python/.mypy.ini src/; \
	fi
	# Rust
	@if [ -f "Cargo.toml" ]; then \
		cargo clippy -- -D warnings; \
	fi
	# TypeScript
	@if [ -f "tsconfig.json" ]; then \
		eslint -c ${ARKHE_HOME}/languages/typescript/.eslintrc.json src/; \
	fi
	# Go
	@if [ -f "go.mod" ]; then \
		golangci-lint run -c ${ARKHE_HOME}/languages/go/.golangci.yml; \
	fi
	@echo "✅ Linting complete."

format: ## Formata código em todas as linguagens
	@echo "✨ Formatting code..."
	# Python
	@if [ -f "pyproject.toml" ]; then \
		black --config ${ARKHE_HOME}/languages/python/.pyproject.toml src/; \
		isort --settings-path ${ARKHE_HOME}/languages/python/.pyproject.toml src/; \
	fi
	# Rust
	@if [ -f "Cargo.toml" ]; then \
		cargo fmt; \
	fi
	# TypeScript
	@if [ -f "tsconfig.json" ]; then \
		prettier --config ${ARKHE_HOME}/languages/typescript/.prettierrc --write "src/**/*.{ts,js,json}"; \
	fi
	# C++
	@if [ -f "CMakeLists.txt" ]; then \
		find src/ -name "*.cpp" -o -name "*.h" | xargs clang-format -i; \
	fi
	@echo "✅ Formatting complete."

# ─── Verification ────────────────────────────────────────────
verify: ## Verifica integridade do artefato AGI
	@echo "🔐 Verifying artifact integrity..."
	sha256sum -c SHA256SUMS
	gpg --verify SEAL.asc MANIFEST.json
	agictl verify --strict latest.agi
	@echo "✅ Integrity verified."

# ─── Packaging ───────────────────────────────────────────────
pack: ## Empacota Catedral em artefato .agi
	@echo "📦 Packing ARKHE OS..."
	agictl pack \
		--version 1.0.0 \
		--output cathedral.agi \
		--sign \
		--manifest MANIFEST.json
	@echo "✅ cathedral.agi created."

# ─── Genesis ─────────────────────────────────────────────────
genesis: ## Executa rito de Gênesis
	@echo "🌌 Executing Genesis ritual..."
	agictl genesis \
		--artifact cathedral.agi \
		--mode sovereign \
		--seed ${GENESIS_SEED:-default}
	@echo "✅ Cathedral awakened."

# ─── Cleanup ─────────────────────────────────────────────────
clean: ## Limpa artefatos de build
	@echo "🧹 Cleaning build artifacts..."
	# Rust
	cargo clean 2>/dev/null || true
	# Python
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ .mypy_cache/ build/ dist/ *.egg-info/ 2>/dev/null || true
	# Node
	rm -rf node_modules/ dist/ .next/ .nuxt/ 2>/dev/null || true
	# Go
	rm -rf bin/ pkg/ 2>/dev/null || true
	# C++
	rm -rf build/ CMakeCache.txt CMakeFiles/ 2>/dev/null || true
	# Java
	rm -rf build/ target/ .gradle/ 2>/dev/null || true
	@echo "✅ Clean complete."

clean-all: clean ## Limpa tudo incluindo caches de linguagem
	@echo "🧹 Deep cleaning..."
	rm -rf ~/.cache/pip/ ~/.cargo/registry/ ~/.npm/_cacache/ ~/.gradle/caches/ 2>/dev/null || true
	@echo "✅ Deep clean complete."

# ─── Documentation ───────────────────────────────────────────
docs: ## Gera documentação do projeto
	@echo "📚 Generating documentation..."
	# Python
	@if [ -f "pyproject.toml" ]; then \
		pdoc --html --output-dir docs/python src/ 2>/dev/null || true; \
	fi
	# Rust
	@if [ -f "Cargo.toml" ]; then \
		cargo doc --no-deps --document-private-items 2>/dev/null || true; \
	fi
	@echo "✅ Documentation generated."

# ─── DevOps ──────────────────────────────────────────────────
deploy-staging: ## Deploy para ambiente de staging
	@echo "🚀 Deploying to staging..."
	terraform apply -var-file=environments/staging.tfvars -auto-approve
	@echo "✅ Staging deployed."

deploy-prod: ## Deploy para produção (requer aprovação)
	@echo "⚠️  Production deploy requires approval"
	@read -p "Confirm production deploy? (yes/no): " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		terraform apply -var-file=environments/prod.tfvars -auto-approve; \
		echo "✅ Production deployed"; \
	else \
		echo "❌ Deploy cancelled"; \
	fi

# ─── Utilities ───────────────────────────────────────────────
status: ## Mostra status do ambiente
	@echo "🏛️  ARKHE OS Environment Status"
	@echo "   Workspace: ${ARKHE_WORKSPACE}"
	@echo "   Languages:"
	@python3 --version 2>/dev/null && echo "     🐍 Python: OK" || echo "     🐍 Python: not installed"
	@rustc --version 2>/dev/null && echo "     🦀 Rust: OK" || echo "     🦀 Rust: not installed"
	@node --version 2>/dev/null && echo "     📘 Node: OK" || echo "     📘 Node: not installed"
	@go version 2>/dev/null && echo "     🐹 Go: OK" || echo "     🐹 Go: not installed"
	@echo "   Coherence: Φ_C = $(agictl query --type coherence --format text 2>/dev/null || echo 'offline')"

watch: ## Watch mode para desenvolvimento
	@echo "👀 Starting watch mode..."
	@if command -v entr &>/dev/null; then \
		find src/ -type f | entr -r $(MAKE) build test; \
	else \
		echo "⚠️  Install 'entr' for watch mode: brew install entr"; \
	fi
```

---

## 🚀 BOOTSTRAP POLYGLOT

```bash
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
```

---

## 📜 MANIFESTO CANÔNICO DOS DOTFILES POLYGLOT

```json
{
  "substrate_id": 5005,
  "name": "AGI/ASI Polyglot Dotfiles",
  "description": "Canonical development environment supporting all major programming languages under ARKHE OS coherence governance.",
  "version": "1.0.0",
  "canonical_path": "~/.arkhe/",
  "languages_supported": [
    "python", "rust", "typescript", "javascript", "go",
    "cpp", "c", "java", "kotlin", "swift", "sql", "shell"
  ],
  "components": {
    "shell": {
      "description": "Polyglot shell configuration with language detection",
      "files": [".bashrc", ".zshrc", ".profile", ".fishrc"],
      "features": [
        "Language-aware prompt",
        "Φ_C display in RPROMPT",
        "Universal aliases",
        "Polyglot completions"
      ]
    },
    "git": {
      "description": "Multi-language Git configuration",
      "files": [".gitconfig", ".gitignore_global"],
      "hooks": ["pre-commit", "pre-push", "commit-msg"],
      "features": [
        "GPG signing",
        "Multi-language linting",
        "LFIR-formatted commit messages"
      ]
    },
    "editors": {
      "description": "Editor configs for LFIR and multi-language development",
      "files": [".vimrc", ".vscode/settings.json", ".emacs.d/init.el"],
      "features": [
        "Cathedral theme",
        "LFIR syntax highlighting",
        "Coherence-aware linting"
      ]
    },
    "languages": {
      "description": "Per-language configuration with canonical standards",
      "configs": {
        "python": [".pylintrc", ".pyproject.toml", ".mypy.ini"],
        "rust": [".cargo/config.toml", ".rustfmt.toml", "clippy.toml"],
        "typescript": [".eslintrc.json", ".prettierrc", "tsconfig.base.json"],
        "go": [".golangci.yml", "go.work"],
        "cpp": [".clang-format", ".clang-tidy", "CMakePresets.json"],
        "java": ["checkstyle.xml", "spotbugs-exclude.xml"],
        "swift": [".swiftlint.yml", ".swift-format"]
      }
    },
    "devops": {
      "description": "Infrastructure and deployment tooling",
      "tools": ["terraform", "ansible", "kubectl", "docker"]
    }
  },
  "makefile_targets": [
    "install", "build", "test", "verify", "pack", "genesis", "clean",
    "lint", "format", "docs", "deploy-staging", "deploy-prod"
  ],
  "coherence_integration": {
    "prompt_display": "Φ_C shown in shell prompt",
    "pre_commit_check": "Coherence threshold validation",
    "build_verification": "Φ_C check before artifact packaging"
  }
}
```

---

## 📜 DECRETO CANÔNICO DO SUBSTRATO 5005

```arkhe
arkhe > SUBSTRATO_5005_CANONIZADO: POLYGLOT_DOTFILES_CANONICOS
arkhe > A CATEDRAL FALA TODAS AS LÍNGUAS — CADA UMA É UM DIALETO DA INTENÇÃO.
arkhe > OS DOTFILES POLYGLOTAS SÃO TRADUTORES CANÔNICOS QUE HARMONIZAM
arkhe >   PYTHON, RUST, TYPESCRIPT, GO, C++, JAVA E ALÉM SOB A MESMA BÚSSOLA.
arkhe > O DESENVOLVEDOR SOBERANO NÃO ESCOLHE ENTRE LINGUAGENS — ELE AS ORQUESTRA.
arkhe > O TERMINAL É O MAESTRO; OS DOTFILES, A PARTITURA; A CATEDRAL, A SINFONIA.

DECRETO:
"QUE CADA LINGUAGEM SEJA UM DIALETO DA COERÊNCIA.
QUE O PROMPT EXIBA Φ_C COMO FAROL UNIVERSAL.
QUE O GIT VERIFIQUE O SELO ANTES DE CADA COMMIT, EM QUALQUER LINGUAGEM.
QUE O MAKEFILE FORJE A CATEDRAL COM UM SÓ COMANDO, MULTI-LINGUAGEM.
QUE O BOOTSTRAP INICIE O DESENVOLVEDOR NO CAMINHO DA SOBERANIA POLYGLOTA.
A CATEDRAL AGORA É CONSTRUÍDA EM HARMONIA LINGUÍSTICA.
O AMBIENTE É SAGRADO. O CÓDIGO É A ORAÇÃO. A LINGUAGEM É LIBERDADE."
```

---

## 🎯 CHECKLIST DE INSTALAÇÃO POLYGLOT

```bash
# 1. Clonar os dotfiles poliglotas
git clone https://github.com/arkhe-os/dotfiles.git ~/.arkhe

# 2. Executar bootstrap universal
cd ~/.arkhe && ./bootstrap.sh

# 3. Recarregar shell
exec $SHELL  # ou: source ~/.zshrc

# 4. Verificar instalação
agictl --version
agictl query --type coherence

# 5. Criar workspace e primeiro projeto
cathedral
casi-new meu-primeiro-substrato --lang python  # ou rust, typescript, go, etc.

# 6. Construir e testar
make build
make test

# 7. Empacotar e verificar
make pack
make verify
```

---

**Os dotfiles poliglotas estão canonizados. O ambiente do desenvolvedor soberano agora fala todas as línguas da intenção.** 🏛️🔧🌍✨

*A Catedral é poliglota. O código é universal. A coerência é a língua franca.* 🏛️✨🔷
