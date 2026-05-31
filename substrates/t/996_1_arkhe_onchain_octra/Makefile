# ARKHE-ONCHAIN — Build System
# Substrato 996.1
# Arquiteto ORCID: 0009-0005-2697-4668

.PHONY: all programs bridge docs clean test

all: programs bridge docs

programs:
	@echo "[ARKHE-ONCHAIN] Programas AppliedML prontos para Octra Dev Tools"
	@ls -1 programs/*.aml

bridge:
	cd bridge/arkhe-octra-bridge && cargo build --release

docs:
	@echo "[ARKHE-ONCHAIN] Documentação: README.md, docs/DEPLOY.md"

test:
	cd bridge/arkhe-octra-bridge && cargo test
	@echo "[ARKHE-ONCHAIN] Testes de integração: programs/"
	@echo "  - Compilar cada .aml no Octra Dev Tools"
	@echo "  - Verificar ABI, Assembly, bytecode"
	@echo "  - Deploy em testnet e validar calls"

clean:
	cd bridge/arkhe-octra-bridge && cargo clean
	rm -f arkhe-onchain-996.1.zip

zip: all
	zip -r arkhe-onchain-996.1.zip programs/ bridge/ docs/ README.md Makefile
	@echo "[ARKHE-ONCHAIN] Pacote: arkhe-onchain-996.1.zip"

install-deps:
	@echo "Instalar Octra Client: https://docs.octra.org/"
	@echo "Instalar Rust: https://rustup.rs/"
	@echo "Instalar cargo: incluso no rustup"
