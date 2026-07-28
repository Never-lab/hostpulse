#!/usr/bin/env bash
# Build Linux client package for HostPulse.
# Usage (from repo root): ./build_linux.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="$ROOT/dist/linux/HostPulse"

rm -rf "$PKG"
mkdir -p "$PKG/bin" "$PKG/config" "$PKG/results"

cp "$ROOT"/bin/*.py "$PKG/bin/"
cp "$ROOT/config/config.example.json" "$PKG/config/"
cp "$ROOT/config/config.example.json" "$PKG/config/config.json"
cp "$ROOT/config/baseline.json" "$PKG/config/"
cp "$ROOT/requirements.txt" "$PKG/"
cp "$ROOT/LICENSE" "$PKG/"
cp "$ROOT/scripts/hostpulse.sh" "$PKG/hostpulse.sh"
chmod +x "$PKG/hostpulse.sh"

ZIP="$ROOT/dist/HostPulse-linux.zip"
mkdir -p "$(dirname "$ZIP")"
rm -f "$ZIP"
(
  cd "$ROOT/dist/linux"
  zip -qr "$ZIP" HostPulse
)

echo ""
echo "Build completata."
echo "  Pacchetto:  $PKG"
echo "  Zip:        $ZIP"
echo ""
echo "Sul server Linux: unzip HostPulse-linux.zip && cd HostPulse && pip install -r requirements.txt && ./hostpulse.sh run --quick --production-safe --out results/report.html"
