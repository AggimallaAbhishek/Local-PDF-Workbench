"""Organize: reorder and/or remove pages of one input PDF.

options:
  pageOrder: [3, 1, 2]   # 1-indexed; output has one page per entry, in this
                         # order. Pages omitted from the list are dropped.
                         # A page number may repeat to duplicate it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool


def _parse_page_order(raw_order: Any, page_count: int) -> list[int]:
    if not isinstance(raw_order, list) or not raw_order:
        raise ToolError("INVALID_OPTIONS", "'pageOrder' must be a non-empty list of page numbers.")

    order = []
    for entry in raw_order:
        page_number = int(entry)
        if page_number < 1 or page_number > page_count:
            raise ToolError(
                "PAGE_OUT_OF_RANGE",
                f"Page {page_number} is out of range for a {page_count}-page document.",
            )
        order.append(page_number)
    return order


def _organize(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Organize requires exactly one input PDF.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)
    order = _parse_page_order(request.options.get("pageOrder"), page_count)

    writer = PdfWriter()
    for page_number in order:
        writer.add_page(reader.pages[page_number - 1])

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_organized.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    warnings = []
    dropped = sorted(set(range(1, page_count + 1)) - set(order))
    if dropped:
        warnings.append(f"Removed {len(dropped)} page(s): {dropped}")

    metadata = {"sourcePageCount": page_count, "outputPageCount": len(order)}
    return [out_path], metadata, warnings


def organize(request: JobRequest) -> JobResult:
    return run_tool(request, _organize)
