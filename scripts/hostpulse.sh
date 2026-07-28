#!/usr/bin/env bash
# HostPulse launcher for Linux client packages (and dev from scripts/).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$HERE/bin/cli.py" ]]; then
  PKG="$HERE"
elif [[ -f "$HERE/../bin/cli.py" ]]; then
  PKG="$(cd "$HERE/.." && pwd)"
else
  echo "HostPulse: cannot locate bin/cli.py (broken package?)" >&2
  exit 1
fi
BIN="$PKG/bin"
export PYTHONPATH="$BIN${PYTHONPATH:+:$PYTHONPATH}"

PY="${HOSTPULSE_PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "HostPulse: python3 not found." >&2
  echo "Install Python 3.10+ then: pip install -r \"$PKG/requirements.txt\"" >&2
  exit 127
fi

check_deps() {
  "$PY" -c "
import sys
sys.path.insert(0, '${BIN}')
from deps_check import require_dependencies
require_dependencies(frozen=False)
"
}

usage() {
  cat <<EOF
HostPulse — hardware/OS benchmark

Usage:
  hostpulse.sh              GUI if DISPLAY is set, else headless quick audit
  hostpulse.sh gui          Start GUI
  hostpulse.sh run [opts]   Headless audit (flags: --profile, --quick, --production-safe, --out, --pdf)
  hostpulse.sh --help       This help

Examples:
  hostpulse.sh run --quick --production-safe --out results/report.html
  hostpulse.sh run --profile db_server --production-safe --out report.html

Requires: pip install -r requirements.txt (once, system-wide or in a venv)
EOF
}

case "${1:-}" in
  -h | --help | help)
    usage
    exit 0
    ;;
  gui)
    shift
    check_deps
    exec "$PY" "$BIN/ui_benchmark.py" "$@"
    ;;
  run)
    shift
    check_deps
    exec "$PY" "$BIN/cli.py" run "$@"
    ;;
  "")
    check_deps
    if [[ -n "${DISPLAY:-}" ]]; then
      exec "$PY" "$BIN/ui_benchmark.py"
    fi
    OUT="$PKG/results/report.html"
    mkdir -p "$PKG/results"
    exec "$PY" "$BIN/cli.py" run --quick --production-safe --out "$OUT"
    ;;
  *)
    echo "Unknown command: $1" >&2
    usage >&2
    exit 2
    ;;
esac
