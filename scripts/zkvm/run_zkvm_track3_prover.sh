#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

WORKDIR="$(mktemp -d -t zkvm_track3_prover_XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "[zee200 track3 prover] WORKDIR=$WORKDIR"
echo ""

cp "$REPO_ROOT/build/bin/test_zkvm_generic_asm_test" "$WORKDIR/ZKMachine"
cp "$REPO_ROOT/benchmarks/track3/track3.s" "$WORKDIR/program.s"
cp "$REPO_ROOT/benchmarks/track3/track3_input" "$WORKDIR/track3_input"

cd "$WORKDIR"
# Party 1: Prover
./ZKMachine -p 1 -P 12345 -a 0 -f program.s < track3_input
