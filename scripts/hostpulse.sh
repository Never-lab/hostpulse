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
VENV_PY="$PKG/.venv/bin/python"
export PYTHONPATH="$BIN${PYTHONPATH:+:$PYTHONPATH}"

PY=""

resolve_python() {
  if [[ -n "$PY" ]]; then
    return
  fi

  if [[ -n "${HOSTPULSE_PYTHON:-}" ]]; then
    PY="$HOSTPULSE_PYTHON"
    if ! command -v "$PY" >/dev/null 2>&1; then
      echo "HostPulse: HOSTPULSE_PYTHON not found: $PY" >&2
      exit 127
    fi
    return
  fi

  if [[ -x "$VENV_PY" ]]; then
    PY="$VENV_PY"
    return
  fi

  local bootstrap="${HOSTPULSE_BOOTSTRAP_PYTHON:-python3}"
  if ! command -v "$bootstrap" >/dev/null 2>&1; then
    echo "HostPulse: python3 not found. Install Python 3.10+." >&2
    exit 127
  fi

  echo "HostPulse: first run — creating .venv and installing dependencies..."
  if ! "$bootstrap" -m venv "$PKG/.venv"; then
    echo "HostPulse: cannot create venv (need python3-venv on Debian/Ubuntu)." >&2
    echo "  sudo apt install python3-venv python3-pip" >&2
    exit 1
  fi

  PY="$VENV_PY"
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q -r "$PKG/requirements.txt"
}

ensure_deps() {
  resolve_python
  if "$PY" -c "
import sys
sys.path.insert(0, '${BIN}')
from deps_check import missing_packages
sys.exit(0 if not missing_packages() else 1)
"; then
    return
  fi

  if [[ -n "${HOSTPULSE_PYTHON:-}" ]]; then
    "$PY" -c "
import sys
sys.path.insert(0, '${BIN}')
from deps_check import require_dependencies
require_dependencies(frozen=False)
"
    return
  fi

  echo "HostPulse: updating dependencies in .venv ..."
  "$PY" -m pip install -q -r "$PKG/requirements.txt"
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

First run creates $PKG/.venv and installs requirements.txt (PEP 668 safe).
Override: HOSTPULSE_PYTHON=/path/to/python ./hostpulse.sh ...
EOF
}

case "${1:-}" in
  -h | --help | help)
    usage
    exit 0
    ;;
  gui)
    shift
    ensure_deps
    exec "$PY" "$BIN/ui_benchmark.py" "$@"
    ;;
  run)
    shift
    ensure_deps
    exec "$PY" "$BIN/cli.py" run "$@"
    ;;
  "")
    ensure_deps
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
