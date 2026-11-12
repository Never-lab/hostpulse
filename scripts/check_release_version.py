#!/usr/bin/env python3
"""Fail if release tag vX.Y.Z does not match bin/version.py and pyproject.toml."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _version_from_py() -> str:
    text = (ROOT / "bin" / "version.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise ValueError("Could not parse __version__ in bin/version.py")
    return match.group(1)


def _version_from_pyproject() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # Scope to [project] so a later tool table cannot steal the match.
    match = re.search(r'(?ms)^\[project\][^\[]*?^version\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError("Could not parse [project].version in pyproject.toml")
    return match.group(1)


def normalize_tag(tag: str) -> str:
    tag = (tag or "").strip()
    if tag.startswith("v") or tag.startswith("V"):
        return tag[1:]
    return tag


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Git tag (e.g. v1.4.1 or 1.4.1)")
    args = parser.parse_args(argv)

    expected = normalize_tag(args.tag)
    if not expected:
        print("ERROR: empty tag after normalizing", file=sys.stderr)
        return 1

    try:
        version_py = _version_from_py()
        version_toml = _version_from_pyproject()
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Bump bin/version.py + pyproject.toml, then retag.", file=sys.stderr)
        return 1

    errors: list[str] = []
    if version_py != expected:
        errors.append(f"bin/version.py={version_py!r} != tag={expected!r}")
    if version_toml != expected:
        errors.append(f"pyproject.toml={version_toml!r} != tag={expected!r}")
    if version_py != version_toml:
        errors.append(f"bin/version.py={version_py!r} != pyproject.toml={version_toml!r}")

    if errors:
        print("ERROR: release version mismatch:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("Bump bin/version.py + pyproject.toml, then retag.", file=sys.stderr)
        return 1

    print(f"OK: tag v{expected} matches bin/version.py and pyproject.toml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
