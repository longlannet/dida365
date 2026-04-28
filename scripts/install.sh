#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() { printf '[dida365] %s\n' "$*"; }
fail() { printf '[dida365] ERROR: %s\n' "$*" >&2; exit 1; }

python_has_requests() {
  "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import requests
PY
}

install_requirements() {
  if "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    log "installing requirements into current python environment"
    "$PYTHON_BIN" -m pip install -r "$BASE_DIR/requirements.txt"
  else
    fail "requests missing and pip is unavailable for $PYTHON_BIN"
  fi
}

log "base dir: $BASE_DIR"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "$PYTHON_BIN not found"

if python_has_requests; then
  log "requests: OK"
else
  log "requests missing; installing locally for current python"
  install_requirements
  python_has_requests || fail "requests still unavailable after install"
  log "requests: OK"
fi

log "running smoke test: dida.py --help"
"$PYTHON_BIN" "$BASE_DIR/scripts/dida.py" --help >/dev/null || fail "smoke test failed"
log "smoke test: OK"
log "python: $(command -v "$PYTHON_BIN" || printf '%s' "$PYTHON_BIN")"
log "install complete"
