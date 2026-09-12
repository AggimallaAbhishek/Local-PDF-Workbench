"""Protect: encrypt a PDF with a password.

options:
  password: str (required)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool


def _protect(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Protect requires exactly one input PDF.")

    password = request.options.get("password")
    if not password:
        raise ToolError("INVALID_OPTIONS", "'password' is required.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    if reader.is_encrypted:
        raise ToolError("ALREADY_ENCRYPTED", "This PDF is already password-protected.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password=str(password))

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_protected.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    return [out_path], {"pageCount": len(reader.pages)}, []


def protect(request: JobRequest) -> JobResult:
    return run_tool(request, _protect)
