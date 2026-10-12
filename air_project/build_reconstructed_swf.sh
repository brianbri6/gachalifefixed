#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${AIR_SDK_HOME:-${FLEX_HOME:-}}"
if [[ -z "$SDK" ]]; then
  echo "Set AIR_SDK_HOME (preferred) or FLEX_HOME to an AIR/Flex SDK containing bin/mxmlc." >&2
  exit 2
fi
MXMLC="$SDK/bin/mxmlc"
if [[ ! -x "$MXMLC" ]]; then
  echo "mxmlc not executable: $MXMLC" >&2
  exit 2
fi
mkdir -p "$ROOT/build"
mapfile -t ALL_CLASSES < <(python - "$ROOT/binary_reconstructed_source/RECONSTRUCTION_REPORT.json" <<'PY_CLASSES'
import json,sys
for row in json.load(open(sys.argv[1],encoding='utf-8'))['generated']:
    print(row['class'])
PY_CLASSES
)
INCLUDE_ARGS=()
for c in "${ALL_CLASSES[@]}"; do INCLUDE_ARGS+=("-includes+=$c"); done
"$MXMLC" \
  -source-path+="$ROOT/binary_reconstructed_source" \
  -default-size 850 500 \
  -default-frame-rate 24 \
  -swf-version=43 \
  -debug=false \
  -compiler.strict=false \
  "${INCLUDE_ARGS[@]}" \
  -output "$ROOT/build/recompiled-code.swf" \
  "$ROOT/binary_reconstructed_source/GachaLifePC_fla/MainTimeline.as"
python "$ROOT/tools/extract_doabc_payload.py" "$ROOT/build/recompiled-code.swf" -o "$ROOT/build/recompiled.abc"
python "$ROOT/tools/rebuild_swf_shell.py" --abc "$ROOT/build/recompiled.abc" -o "$ROOT/build/GachaLifePC-source-rebuilt.swf"
echo "Built: $ROOT/build/GachaLifePC-source-rebuilt.swf"
