"""Split: break one input PDF into several output PDFs.

options:
  mode: "ranges" | "everyPage"
  ranges: [[startPage, endPage], ...]   # 1-indexed, inclusive; required for "ranges"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, require_input_pdf, run_tool


def _parse_ranges(raw_ranges: Any, page_count: int) -> list[tuple[int, int]]:
    if not isinstance(raw_ranges, list) or not raw_ranges:
        raise ToolError("INVALID_OPTIONS", "Split mode 'ranges' requires a non-empty 'ranges' list.")

    ranges: list[tuple[int, int]] = []
    for entry in raw_ranges:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ToolError("INVALID_OPTIONS", f"Each range must be [start, end], got: {entry!r}")
        start, end = int(entry[0]), int(entry[1])
        if start < 1 or end < start or end > page_count:
            raise ToolError(
                "PAGE_OUT_OF_RANGE",
                f"Range {start}-{end} is invalid for a {page_count}-page document.",
            )
        ranges.append((start, end))
    return ranges


def _split(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Split requires exactly one input PDF.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)
    stem = pdf_path.stem
    mode = request.options.get("mode", "everyPage")

    if mode == "ranges":
        ranges = _parse_ranges(request.options.get("ranges"), page_count)
    elif mode == "everyPage":
        ranges = [(i, i) for i in range(1, page_count + 1)]
    else:
        raise ToolError("INVALID_OPTIONS", f"Unknown split mode: {mode!r}")

    outputs: list[Path] = []
    for start, end in ranges:
        writer = PdfWriter()
        for page_number in range(start, end + 1):
            writer.add_page(reader.pages[page_number - 1])

        label = f"p{start}" if start == end else f"p{start}-{end}"
        out_path = workspace / f"{stem}_{label}.pdf"
        with out_path.open("wb") as f:
            writer.write(f)
        outputs.append(out_path)

    metadata = {"sourcePageCount": page_count, "outputCount": len(outputs)}
    return outputs, metadata, []


def split(request: JobRequest) -> JobResult:
    return run_tool(request, _split)
