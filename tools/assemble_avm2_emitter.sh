#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cat "$ROOT/tools/fragments/avm2_to_as3_state.py.part-"* > "$ROOT/tools/avm2_to_as3_state.py"
chmod +x "$ROOT/tools/avm2_to_as3_state.py"
python -m py_compile "$ROOT/tools/avm2_to_as3_state.py"
echo "assembled tools/avm2_to_as3_state.py"
