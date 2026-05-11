#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

WORKDIR="$(mktemp -d -t zkvm_track3_verifier_XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "[zee200 track3 verifier] WORKDIR=$WORKDIR"
echo ""

cp "$REPO_ROOT/build/bin/test_zkvm_generic_asm_test" "$WORKDIR/ZKMachine"
cp "$REPO_ROOT/benchmarks/track3/track3.s" "$WORKDIR/program.s"

cd "$WORKDIR"
# Party 2: Verifier
./ZKMachine -p 2 -P 12345 -a 127.0.0.1 -f program.s
