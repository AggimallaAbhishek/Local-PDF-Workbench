"""Annotate: draw text, rectangles, and lines onto specific pages.

Drawn permanently into the page content via the same reportlab-overlay +
pypdf-merge pattern as watermark/page_numbers (engine/tools/overlay.py) -
not interactive PDF annotation objects, which render inconsistently across
viewers and can't offer the same "what you drew is what ships" guarantee.

options:
  annotations: a non-empty list of, all coordinates in PDF points with a
               bottom-left origin (matching the page's own mediabox):
    {"type": "text", "page": int, "x": num, "y": num, "text": str,
     "fontSize": num (default 14), "color": "#rrggbb" (default "#000000")}
    {"type": "rectangle", "page": int, "x": num, "y": num,
     "width": num, "height": num, "color": "#rrggbb"}
    {"type": "line", "page": int, "x1": num, "y1": num, "x2": num, "y2": num,
     "color": "#rrggbb"}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool
from engine.tools.overlay import stamp_pdf

VALID_TYPES = {"text", "rectangle", "line"}
REQUIRED_NUMBER_FIELDS = {
    "text": ("x", "y"),
    "rectangle": ("x", "y", "width", "height"),
    "line": ("x1", "y1", "x2", "y2"),
}


def _require_number(entry: dict[str, Any], key: str) -> float:
    value = entry.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ToolError("INVALID_OPTIONS", f"Annotation field '{key}' must be a number, got: {value!r}")
    return float(value)


def _parse_color(raw: Any) -> HexColor:
    try:
        return HexColor(str(raw))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("INVALID_OPTIONS", f"Invalid color: {raw!r}") from exc


def _parse_annotations(raw: Any, page_count: int) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise ToolError("INVALID_OPTIONS", "'annotations' must be a non-empty list.")

    parsed = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise ToolError("INVALID_OPTIONS", "Each annotation must be an object.")

        kind = entry.get("type")
        if kind not in VALID_TYPES:
            raise ToolError("INVALID_OPTIONS", f"Unknown annotation type: {kind!r}")

        page = entry.get("page")
        if not isinstance(page, int) or isinstance(page, bool) or page < 1 or page > page_count:
            raise ToolError(
                "PAGE_OUT_OF_RANGE",
                f"Annotation page {page!r} is out of range for a {page_count}-page document.",
            )

        for field in REQUIRED_NUMBER_FIELDS[kind]:
            _require_number(entry, field)
        if kind == "text" and not str(entry.get("text", "")).strip():
            raise ToolError("INVALID_OPTIONS", "A text annotation requires non-empty 'text'.")
        _parse_color(entry.get("color", "#000000"))

        parsed.append(entry)
    return parsed


def _draw_annotation(c: canvas.Canvas, entry: dict[str, Any]) -> None:
    color = _parse_color(entry.get("color", "#000000"))
    kind = entry["type"]

    if kind == "text":
        c.setFillColor(color)
        c.setFont("Helvetica", float(entry.get("fontSize", 14)))
        c.drawString(_require_number(entry, "x"), _require_number(entry, "y"), str(entry["text"]))
    elif kind == "rectangle":
        c.setStrokeColor(color)
        c.setLineWidth(2)
        c.rect(
            _require_number(entry, "x"),
            _require_number(entry, "y"),
            _require_number(entry, "width"),
            _require_number(entry, "height"),
            fill=0,
            stroke=1,
        )
    elif kind == "line":
        c.setStrokeColor(color)
        c.setLineWidth(2)
        c.line(
            _require_number(entry, "x1"),
            _require_number(entry, "y1"),
            _require_number(entry, "x2"),
            _require_number(entry, "y2"),
        )


def _annotate(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Annotate requires exactly one input PDF.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)
    annotations = _parse_annotations(request.options.get("annotations"), page_count)

    by_page: dict[int, list[dict[str, Any]]] = {}
    for entry in annotations:
        by_page.setdefault(entry["page"], []).append(entry)

    def draw(c: canvas.Canvas, _width: float, _height: float, page_number: int, _total: int) -> None:
        for entry in by_page.get(page_number, []):
            _draw_annotation(c, entry)

    writer = stamp_pdf(reader, draw)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_annotated.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    metadata = {"pageCount": page_count, "annotationCount": len(annotations)}
    return [out_path], metadata, []


def annotate(request: JobRequest) -> JobResult:
    return run_tool(request, _annotate)
