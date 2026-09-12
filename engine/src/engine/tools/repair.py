"""Repair: attempt to fix a damaged PDF.

Uses pikepdf (backed by qpdf), which recovers many real-world corruption
cases - stale or broken xref tables, mismatched trailers - by rebuilding the
document structure from whatever objects it can still find, then re-saving.
Severely damaged files (truncated mid-object, non-PDF content) can't be
recovered and are reported as such rather than silently producing garbage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pikepdf

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool


def _repair(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Repair requires exactly one input PDF.")

    pdf_path = require_input_pdf(request.inputs[0])

    try:
        pdf = pikepdf.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREPAIRABLE", f"Could not recover {pdf_path.name}: {exc}") from exc

    try:
        page_count = len(pdf.pages)
        if page_count == 0:
            raise ToolError("UNREPAIRABLE", "No pages could be recovered from this file.")

        filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_repaired.pdf")
        out_path = workspace / filename
        pdf.save(str(out_path))
    finally:
        pdf.close()

    return [out_path], {"pageCount": page_count}, []


def repair(request: JobRequest) -> JobResult:
    return run_tool(request, _repair)
