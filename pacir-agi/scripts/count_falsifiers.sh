#!/usr/bin/env bash
set -euo pipefail
count=$(rg -c '^pub fn falsify_agi_' crates/pacir-agi-core/src/falsifiers.rs)
[ "$count" -eq 12 ] || { echo "expected 12 falsifiers, found $count" >&2; exit 1; }
echo "12 falsifiers verified"
