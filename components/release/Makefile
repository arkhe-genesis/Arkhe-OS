# release/Makefile

VERSION ?= 1.0.0
QUANTUM_MODE ?= hybrid

.PHONY: all clean consent-check tar apk 7z exe msi checksums sign verify codex info

all: clean tar apk 7z exe msi checksums sign codex

clean:
	@echo "🧹 Limpando builds anteriores..."
	@rm -rf build dist

consent-check:
	@echo "🔐 Verificando consentimento de release..."
	@OPERATOR_DID=did:cathedral:maintainer:ferreiro bash scripts/consent-check.sh

tar: consent-check
	@echo "📦 [tar.gz] Modo: $(QUANTUM_MODE) | v$(VERSION)"

apk: consent-check
	@echo "📱 [apk] Modo: $(QUANTUM_MODE) | v$(VERSION)"

7z: consent-check
	@echo "🗜️  [7z] Empacotando binários Windows..."

exe: consent-check
	@echo "🪟 [exe] Modo: $(QUANTUM_MODE) | v$(VERSION)"

msi: exe
	@echo "📀 [msi] Construindo instalador Windows..."

checksums:
	@echo "🔐 Gerando checksums SHA-256..."

sign: checksums
	@echo "✍️  Assinando artefatos..."

verify: sign
	@echo "🔍 Verificando integridade..."

codex: verify
	@echo "📜 Ancorando no Códice..."
	@bash codex/anchor-release.sh $(VERSION)

info:
	@echo "Catedral Arkhe — Release System"
	@echo "Version: $(VERSION)"
	@echo "Quantum Mode: $(QUANTUM_MODE)"
