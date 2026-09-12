"""Crop: trim page margins.

options:
  margins: {top, right, bottom, left} in points (default 0 each)
  pages: "all" | [1, 3] (default "all")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, resolve_pages, run_tool

MARGIN_KEYS = ("top", "right", "bottom", "left")


def _parse_margins(raw_margins: Any) -> dict[str, float]:
    margins = {key: 0.0 for key in MARGIN_KEYS}
    if raw_margins is None:
        return margins
    if not isinstance(raw_margins, dict):
        raise ToolError("INVALID_OPTIONS", "'margins' must be an object with top/right/bottom/left.")

    for key in MARGIN_KEYS:
        if key not in raw_margins:
            continue
        try:
            value = float(raw_margins[key])
        except (TypeError, ValueError):
            raise ToolError("INVALID_OPTIONS", f"Margin '{key}' must be a number.") from None
        if value < 0:
            raise ToolError("INVALID_OPTIONS", f"Margin '{key}' must not be negative.")
        margins[key] = value
    return margins


def _crop(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Crop requires exactly one input PDF.")

    margins = _parse_margins(request.options.get("margins"))

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)
    target_pages = resolve_pages(request.options.get("pages"), page_count)

    writer = PdfWriter()
    for index, page in enumerate(reader.pages, start=1):
        if index in target_pages:
            box = page.mediabox
            left = float(box.left) + margins["left"]
            bottom = float(box.bottom) + margins["bottom"]
            right = float(box.right) - margins["right"]
            top = float(box.top) - margins["top"]
            if left >= right or bottom >= top:
                raise ToolError("MARGINS_TOO_LARGE", f"Margins leave no visible area on page {index}.")

            page.mediabox.lower_left = (left, bottom)
            page.mediabox.upper_right = (right, top)
            page.cropbox.lower_left = (left, bottom)
            page.cropbox.upper_right = (right, top)
        writer.add_page(page)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_cropped.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    metadata = {"pageCount": page_count, "croppedPages": sorted(target_pages)}
    return [out_path], metadata, []


def crop(request: JobRequest) -> JobResult:
    return run_tool(request, _crop)
