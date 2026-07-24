from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pdf_export import PdfExportError, find_browser, html_file_to_pdf


def test_find_browser_returns_string_or_none() -> None:
    browser = find_browser()
    assert browser is None or isinstance(browser, str)


def test_html_to_pdf_missing_file() -> None:
    with pytest.raises(PdfExportError, match="HTML not found"):
        html_file_to_pdf("no-such-file.html")


def test_html_to_pdf_no_browser(tmp_path: Path) -> None:
    html = tmp_path / "r.html"
    html.write_text("<html><body>ok</body></html>", encoding="utf-8")
    with patch("pdf_export.find_browser", return_value=None):
        with pytest.raises(PdfExportError, match="No Edge/Chrome"):
            html_file_to_pdf(html, tmp_path / "r.pdf")
