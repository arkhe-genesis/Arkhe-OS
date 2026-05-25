#!/bin/bash
set -e

echo "Building Go binary..."
cd cmd/arkhe
go build -o arkhe_bin .
cd ../..

echo "Building Rust binary..."
cd scripts
cargo build --release
cd ..

echo "Building Python substrate..."
cd substrates/9012_arkhe_ipython
python3 setup.py bdist_wheel
cd ../..

echo "Generating manifest..."
cat << 'MANIFEST' > build_manifest.json
{
    "go_binaries": [
        "cmd/arkhe/arkhe_bin"
    ],
    "rust_binaries": [
        "target/release/libscripts.rlib"
    ],
    "python_substrates": [
        "substrates/9012_arkhe_ipython/dist/arkhe_ipython-1.0.0-py3-none-any.whl"
    ],
    "gguf_artifacts": [
        "build/arkhe.gguf",
        "build/arkhe_gguf_manifest.json"
    ]
}
MANIFEST
echo "Done!"
