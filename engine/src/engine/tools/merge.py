"""Merge: combine multiple input PDFs, in the given order, into one file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool


def _merge(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) < 2:
        raise ToolError("INVALID_INPUT", "Merge requires at least two input PDFs.")

    writer = PdfWriter()
    total_pages = 0
    for raw_path in request.inputs:
        pdf_path = require_input_pdf(raw_path)
        try:
            reader = PdfReader(str(pdf_path))
        except Exception as exc:  # noqa: BLE001 - normalize any parser error
            raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

        for page in reader.pages:
            writer.add_page(page)
        total_pages += len(reader.pages)

    filename = output_filename(request.options, "outputFilename", "merged.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    metadata = {"pageCount": total_pages, "sourceCount": len(request.inputs)}
    return [out_path], metadata, []


def merge(request: JobRequest) -> JobResult:
    return run_tool(request, _merge)
