"""HTML → PDF via headless Chromium/Edge (no PDF library dependency)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional


class PdfExportError(RuntimeError):
    pass


def _candidate_browsers() -> Iterable[str]:
    env = os.environ.get("HOSTPULSE_BROWSER", "").strip()
    if env:
        yield env
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        pf86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        for path in (
            shutil.which("msedge"),
            shutil.which("chrome"),
            os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
        ):
            if path:
                yield path
    else:
        for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
            found = shutil.which(name)
            if found:
                yield found


def find_browser() -> Optional[str]:
    seen = set()
    for path in _candidate_browsers():
        if path in seen:
            continue
        seen.add(path)
        if os.path.isfile(path):
            return path
    return None


def html_file_to_pdf(html_path: str | Path, pdf_path: str | Path | None = None) -> Path:
    """Print an offline HTML file to PDF. Raises PdfExportError on failure."""
    html = Path(html_path).resolve()
    if not html.is_file():
        raise PdfExportError(f"HTML not found: {html}")
    out = Path(pdf_path).resolve() if pdf_path else html.with_suffix(".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    browser = find_browser()
    if not browser:
        raise PdfExportError(
            "No Edge/Chrome found for PDF export. Install Microsoft Edge or Google Chrome, "
            "or set HOSTPULSE_BROWSER to the browser executable."
        )

    uri = html.as_uri()
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out}",
        uri,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PdfExportError(f"PDF export failed: {exc}") from exc

    if not out.is_file() or out.stat().st_size < 100:
        err = (proc.stderr or proc.stdout or "").strip()
        raise PdfExportError(f"PDF was not created ({browser}). {err}")
    return out
