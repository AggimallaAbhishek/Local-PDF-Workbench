"""Watermark: stamp semi-transparent text onto every (or selected) page.

options:
  text: str (required)
  opacity: float, 0 < opacity <= 1 (default 0.3)
  fontSize: int (default 40)
  position: "diagonal" | "center" (default "diagonal")
  pages: "all" | [1, 3] (default "all")
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, resolve_pages, run_tool
from engine.tools.overlay import stamp_pdf


def _watermark(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Watermark requires exactly one input PDF.")

    text = request.options.get("text")
    if not text:
        raise ToolError("INVALID_OPTIONS", "'text' is required.")

    opacity = float(request.options.get("opacity", 0.3))
    if not 0 < opacity <= 1:
        raise ToolError("INVALID_OPTIONS", "'opacity' must be between 0 (exclusive) and 1.")

    font_size = int(request.options.get("fontSize", 40))
    diagonal = request.options.get("position", "diagonal") != "center"

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)
    target_pages = resolve_pages(request.options.get("pages"), page_count)

    def draw(c: canvas.Canvas, width: float, height: float, page_number: int, _total: int) -> None:
        if page_number not in target_pages:
            return
        c.saveState()
        c.setFont("Helvetica-Bold", font_size)
        c.setFillColor(Color(0, 0, 0, alpha=opacity))
        c.translate(width / 2, height / 2)
        if diagonal:
            c.rotate(math.degrees(math.atan2(height, width)))
        c.drawCentredString(0, 0, str(text))
        c.restoreState()

    writer = stamp_pdf(reader, draw)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_watermarked.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    metadata = {"pageCount": page_count, "stampedPages": sorted(target_pages)}
    return [out_path], metadata, []


def watermark(request: JobRequest) -> JobResult:
    return run_tool(request, _watermark)
