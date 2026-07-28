#!/usr/bin/env bash
# Local verify for HostPulse (Linux / WSL).
# Usage (from repo root):
#   ./scripts/verify_local.sh
#   BUILD_LINUX=1 ./scripts/verify_local.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

echo "==> Install deps"
"$PY" -m pip install -q -r requirements.txt -r requirements-dev.txt

echo "==> Ruff"
"$PY" -m ruff check bin tests

echo "==> compileall"
"$PY" -m compileall -q bin

echo "==> Pytest"
"$PY" -m pytest -q

echo "==> Import smoke (PYTHONPATH=bin)"
PYTHONPATH=bin "$PY" -c "import app_paths, engine, reporter_generator, version, ui_benchmark; print('imports ok', version.__version__)"

if [[ "${BUILD_LINUX:-}" == "1" ]]; then
  echo "==> Linux package build"
  chmod +x build_linux.sh scripts/hostpulse.sh
  ./build_linux.sh
  PKG="$ROOT/dist/linux/HostPulse"
  test -x "$PKG/hostpulse.sh"
  echo "==> Linux headless smoke"
  HOSTPULSE_PYTHON="$PY" "$PKG/hostpulse.sh" run --quick --production-safe --out /tmp/hostpulse-smoke.html
  test -f /tmp/hostpulse-smoke.html
  echo "report ok: /tmp/hostpulse-smoke.html"
fi

echo ""
echo "verify_local OK"
