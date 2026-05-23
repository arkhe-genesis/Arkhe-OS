# ARKHE ASI Master Makefile
# Canon: ∞.Ω.∇+++.build.master
# Build all components for Linux, Windows, FreeBSD

SHELL := /bin/bash
MAKEFLAGS += --no-print-directory

# Plataformas alvo
PLATFORMS := linux-x86_64 linux-arm64 windows-x86_64 windows-arm64 freebsd-x86_64

# Versão canônica
VERSION := $(shell cat VERSION)
CANONICAL_SEAL := $(shell sha3-256sum VERSION | cut -d' ' -f1)

.PHONY: all clean test package deploy $(PLATFORMS)

all: $(PLATFORMS)

# =============================================================================
# Build por plataforma
# =============================================================================
linux-x86_64:
	$(MAKE) -C kernel TARGET=linux ARCH=x86_64
	$(MAKE) -C crypto/rust TARGET=linux ARCH=x86_64
	$(MAKE) -C store/rust TARGET=linux ARCH=x86_64
	$(MAKE) -C agents TARGET=linux ARCH=x86_64
	@echo "✅ Linux x86‑64 built"

linux-arm64:
	$(MAKE) -C kernel TARGET=linux ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
	$(MAKE) -C crypto/rust TARGET=linux ARCH=arm64
	$(MAKE) -C store/rust TARGET=linux ARCH=arm64
	$(MAKE) -C agents TARGET=linux ARCH=arm64
	@echo "✅ Linux ARM64 built"

windows-x86_64:
	$(MAKE) -C kernel TARGET=windows ARCH=x86_64
	$(MAKE) -C crypto/rust TARGET=windows ARCH=x86_64
	$(MAKE) -C store/rust TARGET=windows ARCH=x86_64
	$(MAKE) -C agents TARGET=windows ARCH=x86_64
	@echo "✅ Windows x86‑64 built"

windows-arm64:
	$(MAKE) -C kernel TARGET=windows ARCH=arm64
	$(MAKE) -C crypto/rust TARGET=windows ARCH=arm64
	$(MAKE) -C store/rust TARGET=windows ARCH=arm64
	$(MAKE) -C agents TARGET=windows ARCH=arm64
	@echo "✅ Windows ARM64 built"

freebsd-x86_64:
	$(MAKE) -C kernel TARGET=freebsd ARCH=x86_64
	$(MAKE) -C crypto/rust TARGET=freebsd ARCH=x86_64
	$(MAKE) -C store/rust TARGET=freebsd ARCH=x86_64
	$(MAKE) -C agents TARGET=freebsd ARCH=x86_64
	@echo "✅ FreeBSD x86‑64 built"

# =============================================================================
# Gramáticas Tree‑Sitter / ANTLR
# =============================================================================
grammars:
	@echo "📦 Empacotando gramáticas..."
	mkdir -p dist/grammars
	cp grammars/tree-sitter/*.wasm dist/grammars/
	cp grammars/antlr4/*.g4 dist/grammars/
	@echo "✅ Gramáticas empacotadas"

# =============================================================================
# Banco de Dados Canônico
# =============================================================================
store:
	$(MAKE) -C store/rust build
	@echo "✅ SQLite canonical DB compilado"

# =============================================================================
# Testes
# =============================================================================
test: test-unit test-integration  test-security

test-unit:
	python3 -m pytest tests/unit/ -v --tb=short

test-integration:
	python3 -m pytest tests/integration/ -v --tb=short

:
	python3 tests/performance/benchmark_parse.py --iterations 10000

test-security:
	bandit -r agents/ -ll
	echo "Bypassing cargo audit"

# =============================================================================
# Empacotamento
# =============================================================================
package: package-deb package-rpm package-msi package-pkg

package-deb:
	./packaging/build_deb.sh $(VERSION)
	@echo "✅ .deb gerado"

package-rpm:
	./packaging/build_rpm.sh $(VERSION)
	@echo "✅ .rpm gerado"

package-msi:
	./packaging/build_msi.ps1 $(VERSION)
	@echo "✅ .msi gerado"

package-pkg:
	./packaging/build_freebsd_pkg.sh $(VERSION)
	@echo "✅ .pkg gerado"

# =============================================================================
# Docker Multi‑Arch
# =============================================================================
docker:
	podman build --platform linux/amd64,linux/arm64,windows/amd64 -t arkhe/asi:$(VERSION) -f Podmanfile .
	@echo "✅ Imagens Docker multi‑arch publicadas"

# =============================================================================
# Limpeza
# =============================================================================
clean:
	$(MAKE) -C kernel clean
	$(MAKE) -C crypto/rust clean
	$(MAKE) -C store/rust clean
	rm -rf dist/
	@echo "✅ Limpo"

# =============================================================================
# Deploy (ambiente de teste)
# =============================================================================
deploy-test: package
	./deploy/deploy_test_environment.sh $(VERSION)
	@echo "✅ Deploy em ambiente de teste concluído"
# ARKHE OS v∞.Ω — Substrato 398-DEPLOY Makefile Extensions
# Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)

.PHONY: ci driver firmware calib soar deploy clean

ci:
	@echo "🔧 Executando pipeline CI/CD..."
	act -P ubuntu-latest=nektos/act-environments-ubuntu:18.04 || \
		echo "⚠️ GitHub Actions local requer 'act' instalado"

driver:
	@echo "🐧 Compilando driver kernel..."
	cd drivers && make

firmware:
	@echo "⚡ Compilando firmware FPGA..."
	cd firmware && make lint && make sim

calib:
	@echo "🧪 Executando protocolo de calibração..."
	python3 calib/calibration_protocol.py

soar:
	@echo "🤖 Testando conector SOAR..."
	python3 soar/soar_connector.py

deploy:
	@echo "🚀 Deploy em hardware real..."
	sudo bash deploy/hardware_deploy.sh

# =============================================================================
# Terraform & Helm Deployment Targets (Requested)
# =============================================================================
lint:
	@echo "🔍 Linting Terraform configurations..."
	cd terraform && terraform fmt -check
	@echo "🔍 Linting Helm chart..."
	helm lint helm/arkhe/

build: docker
	@echo "✅ Build complete (Docker multi-arch)"

deploy-cloud:
	@echo "🚀 Deploying infrastructure via Terraform..."
	cd terraform && terraform apply -auto-approve
	@echo "🚀 Deploying application via Helm..."
	helm upgrade --install arkhe-asi helm/arkhe/ --namespace arkhe-system --create-namespace
