"""PDF to JPG: export pages as JPEG images.

options:
  dpi: int, 36-600 (default 150)
  pages: "all" | [1, 3] (default "all")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, require_input_pdf, run_tool

DEFAULT_DPI = 150


def _resolve_pages(raw_pages: Any, page_count: int) -> list[int]:
    if raw_pages in (None, "all"):
        return list(range(1, page_count + 1))
    if not isinstance(raw_pages, list) or not raw_pages:
        raise ToolError("INVALID_OPTIONS", "'pages' must be \"all\" or a non-empty list of page numbers.")

    pages = []
    for entry in raw_pages:
        page_number = int(entry)
        if page_number < 1 or page_number > page_count:
            raise ToolError(
                "PAGE_OUT_OF_RANGE",
                f"Page {page_number} is out of range for a {page_count}-page document.",
            )
        pages.append(page_number)
    return pages


def _pdf_to_jpg(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "PDF to JPG requires exactly one input PDF.")

    dpi = int(request.options.get("dpi", DEFAULT_DPI))
    if not 36 <= dpi <= 600:
        raise ToolError("INVALID_OPTIONS", "'dpi' must be between 36 and 600.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        doc = pymupdf.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    try:
        page_count = doc.page_count
        pages = _resolve_pages(request.options.get("pages"), page_count)
        zoom = dpi / 72.0

        outputs: list[Path] = []
        for page_number in pages:
            page = doc[page_number - 1]
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            out_path = workspace / f"{pdf_path.stem}_p{page_number}.jpg"
            pix.save(str(out_path))
            outputs.append(out_path)
    finally:
        doc.close()

    metadata = {"pageCount": page_count, "renderedPages": pages, "dpi": dpi}
    return outputs, metadata, []


def pdf_to_jpg(request: JobRequest) -> JobResult:
    return run_tool(request, _pdf_to_jpg)
