"""Page numbers: stamp a page-number label onto every page.

options:
  position: "bottom-center" | "bottom-left" | "bottom-right"
           | "top-center" | "top-left" | "top-right" (default "bottom-center")
  startAt: int (default 1) — the number printed on the first page
  format: str (default "{page} / {total}") — Python format string;
          "{page}" and "{total}" are the only placeholders
  fontSize: int (default 10)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool
from engine.tools.overlay import stamp_pdf

MARGIN = 24

# Each entry maps a position name to (x, y, alignment) given the page size.
POSITIONS = {
    "bottom-center": lambda w, h: (w / 2, MARGIN, "center"),
    "bottom-right": lambda w, h: (w - MARGIN, MARGIN, "right"),
    "bottom-left": lambda w, h: (MARGIN, MARGIN, "left"),
    "top-center": lambda w, h: (w / 2, h - MARGIN, "center"),
    "top-right": lambda w, h: (w - MARGIN, h - MARGIN, "right"),
    "top-left": lambda w, h: (MARGIN, h - MARGIN, "left"),
}


def _page_numbers(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Add page numbers requires exactly one input PDF.")

    position = request.options.get("position", "bottom-center")
    if position not in POSITIONS:
        raise ToolError("INVALID_OPTIONS", f"'position' must be one of {sorted(POSITIONS)}.")

    start_at = int(request.options.get("startAt", 1))
    font_size = int(request.options.get("fontSize", 10))
    label_format = request.options.get("format", "{page} / {total}")

    try:
        label_format.format(page=1, total=1)
    except (KeyError, IndexError, ValueError) as exc:
        raise ToolError("INVALID_OPTIONS", f"Invalid 'format' string: {exc}") from exc

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)

    def draw(c: canvas.Canvas, width: float, height: float, page_number: int, total: int) -> None:
        x, y, align = POSITIONS[position](width, height)
        label = label_format.format(page=start_at + page_number - 1, total=total)
        c.setFont("Helvetica", font_size)
        if align == "center":
            c.drawCentredString(x, y, label)
        elif align == "right":
            c.drawRightString(x, y, label)
        else:
            c.drawString(x, y, label)

    writer = stamp_pdf(reader, draw)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_numbered.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    return [out_path], {"pageCount": page_count}, []


def page_numbers(request: JobRequest) -> JobResult:
    return run_tool(request, _page_numbers)
