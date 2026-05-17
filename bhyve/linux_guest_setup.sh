#!/bin/bash
set -e

echo "Setting up Linux Guest for CUDA..."
# Install generic CUDA dependencies if we are inside a debian/ubuntu guest
if command -v apt-get >/dev/null; then
    apt-get update
    apt-get install -y nvidia-cuda-toolkit || echo "CUDA toolkit not available in repo, skipping for test"
fi
echo "Setup complete"
