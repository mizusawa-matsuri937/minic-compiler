#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
MINIC_PYTHON="${MINIC_PYTHON:-python3}"
MINIC_BUILD_DIR="${MINIC_BUILD_DIR:-$PROJECT_ROOT/build/minic}"
MINIC_OUT_DIR="${MINIC_OUT_DIR:-$PROJECT_ROOT/out/demo}"

"$MINIC_PYTHON" -m ccgen --lex rules/minic.lex --grammar rules/minic.grammar --out "$MINIC_BUILD_DIR"
"$MINIC_PYTHON" -m minic examples/demo.mc --frontend "$MINIC_BUILD_DIR" --out "$MINIC_OUT_DIR"
for artifact in tokens.txt tokens.json ast.json ast.txt ast.html ast.dot demo.ll demo.opt.ll demo.s demo; do
    printf '%s\n' "$MINIC_OUT_DIR/$artifact"
done
"$MINIC_OUT_DIR/demo"
