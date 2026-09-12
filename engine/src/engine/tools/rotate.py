"""Rotate: rotate specified pages of one input PDF by a fixed angle.

options:
  angle: 90 | 180 | 270 (clockwise)
  pages: "all" | [1, 3, 5]   # 1-indexed; defaults to "all"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, resolve_pages, run_tool

VALID_ANGLES = {90, 180, 270}


def _rotate(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Rotate requires exactly one input PDF.")

    angle = request.options.get("angle")
    if angle not in VALID_ANGLES:
        raise ToolError("INVALID_OPTIONS", f"'angle' must be one of {sorted(VALID_ANGLES)}, got: {angle!r}")

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
            page.rotate(angle)
        writer.add_page(page)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_rotated.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    metadata = {"pageCount": page_count, "rotatedPages": sorted(target_pages)}
    return [out_path], metadata, []


def rotate(request: JobRequest) -> JobResult:
    return run_tool(request, _rotate)
