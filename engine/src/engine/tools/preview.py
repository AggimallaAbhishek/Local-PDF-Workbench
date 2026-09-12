"""Preview: render page thumbnails for one input PDF as PNG files.

Backs the tool workspace's Preview panel and page-selection UI (PLAN.md §6)
for split/rotate/organize. Not itself a page-editing tool, so it reuses
`run_tool` only for input/output-dir validation and atomic move — every
rendered page is a real "output" of this job.

options:
  maxWidthPx: int (default 240) — thumbnails are capped to this width.
  pages: [1, 3] | omitted for all pages
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, require_input_pdf, run_tool

DEFAULT_MAX_WIDTH_PX = 240


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


def _preview(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Preview requires exactly one input PDF.")

    pdf_path = require_input_pdf(request.inputs[0])
    max_width = int(request.options.get("maxWidthPx") or DEFAULT_MAX_WIDTH_PX)

    try:
        doc = pymupdf.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    try:
        page_count = doc.page_count
        pages = _resolve_pages(request.options.get("pages"), page_count)

        outputs: list[Path] = []
        page_sizes: dict[str, list[float]] = {}
        for page_number in pages:
            page = doc[page_number - 1]
            zoom = max_width / page.rect.width if page.rect.width else 1.0
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))

            out_path = workspace / f"{pdf_path.stem}_thumb_p{page_number}.png"
            pix.save(str(out_path))
            outputs.append(out_path)
            page_sizes[str(page_number)] = [page.rect.width, page.rect.height]
    finally:
        doc.close()

    metadata = {"pageCount": page_count, "renderedPages": pages, "pageSizes": page_sizes}
    return outputs, metadata, []


def preview(request: JobRequest) -> JobResult:
    return run_tool(request, _preview)
