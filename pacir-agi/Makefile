CARGO = cargo
PYTHON = python3
.PHONY: build test lint count verify serve
build:
	$(CARGO) build --workspace
test:
	$(CARGO) test --workspace
	PYTHONPATH=python $(PYTHON) -m pytest python/tests
lint:
	$(CARGO) fmt --all -- --check
	$(CARGO) clippy --workspace -- -D warnings
count:
	bash scripts/count_falsifiers.sh
verify: lint count test
serve:
	$(CARGO) run -p pacir-agi-cli -- list
