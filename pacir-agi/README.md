# PACIR-AGI

PACIR-AGI is a standalone Rust and Python workspace for producing and checking a
zero-tensor `agi.gguf` routing manifest. The workspace provides twelve executable
falsifiers, BRICS governance invariants, a five-stage verification pipeline, a
router/cache inference prototype, and a small training metadata pipeline.

## Quick start

```sh
cd pacir-agi
cargo test --workspace
PYTHONPATH=python python3 -m pytest python/tests
make verify
```

`config/training_config.json` deliberately starts with 1,000 experts. The 250,000
expert count is an explicit governance invariant, not an implied deployment claim.
