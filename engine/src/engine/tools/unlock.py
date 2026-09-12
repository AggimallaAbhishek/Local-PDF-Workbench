"""Unlock: remove a password you already know.

options:
  password: str (required)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool


def _unlock(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Unlock requires exactly one input PDF.")

    password = request.options.get("password")
    if not password:
        raise ToolError("INVALID_OPTIONS", "'password' is required.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    if not reader.is_encrypted:
        raise ToolError("NOT_ENCRYPTED", "This PDF is not password-protected.")

    if reader.decrypt(str(password)) == 0:
        raise ToolError("WRONG_PASSWORD", "The password did not unlock this PDF.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_unlocked.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    return [out_path], {"pageCount": len(reader.pages)}, []


def unlock(request: JobRequest) -> JobResult:
    return run_tool(request, _unlock)
