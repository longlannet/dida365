#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="$BASE_DIR/config"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUN_SMOKE="${RUN_SMOKE:-1}"

log() { printf '[dida365] %s\n' "$*"; }
fail() { printf '[dida365] ERROR: %s\n' "$*" >&2; exit 1; }

python_has_requests() {
  "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import requests
PY
}

log "base dir: $BASE_DIR"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "$PYTHON_BIN not found"
python_has_requests || fail "requests not available for $PYTHON_BIN. Run scripts/install.sh"
log "python: OK ($(command -v "$PYTHON_BIN" || printf '%s' "$PYTHON_BIN"))"
log "requests: OK"

"$PYTHON_BIN" -m py_compile "$BASE_DIR/scripts/dida.py" || fail "dida.py syntax check failed"
log "syntax: OK"

if [ -f "$CONFIG_DIR/token.json" ]; then
  log "config/token.json: OK"
else
  log "config/token.json: MISSING (run get_auth_url + exchange_token)"
fi

if [ "$RUN_SMOKE" = "1" ]; then
  log "running smoke test"
  "$PYTHON_BIN" "$BASE_DIR/scripts/dida.py" project list >/dev/null || fail "smoke test failed"
  log "smoke test: OK"
fi

log "check complete"
