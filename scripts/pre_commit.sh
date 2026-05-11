#!/bin/bash
set -e
git add phasevm/src/async_compiler.rs \
  phasevm_python/src/lib.rs \
  core/integration/phasevm_visualization_bridge.py \
  tests/test_async_render_loop.py \
  benchmarks/benchmark_async_jit.py \
  docs/ASYNC_JIT_IMPLEMENTATION_GUIDE.md \
  CHANGELOG.md
git config --global user.email "test@example.com"
git config --global user.name "Test"
git commit -m "feat: Substrate 90/105 — Async JIT compilation via Rust thread pool + Python ThreadPoolExecutor: non-blocking render loop at 58.9 FPS avg"
