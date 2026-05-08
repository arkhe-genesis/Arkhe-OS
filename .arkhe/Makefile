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