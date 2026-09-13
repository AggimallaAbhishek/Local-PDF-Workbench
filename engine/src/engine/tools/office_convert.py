"""Shared plumbing for Office-document-to-PDF conversion via headless
LibreOffice (`soffice --convert-to pdf`).

Only the "native format -> PDF" direction is implemented. The reverse
(PDF -> editable Word/Excel/PowerPoint) does not work with LibreOffice:
headless soffice opens a PDF into Draw, and Draw has no export filter to
Writer/Calc/Impress formats at all - confirmed directly (docx, odt, xlsx,
and pptx targets all fail with "no export filter"), not a filter-naming
issue. Shipping that direction would mean either failing every time or
producing something misleadingly poor, so it isn't offered.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, run_tool

SOFFICE_TIMEOUT_SECONDS = 120
FORMAT_WARNING = (
    "Office conversions preserve most text and layout but may not match the original exactly - "
    "review the result before relying on it."
)


def require_input_office_file(path: str, allowed_suffixes: set[str]) -> Path:
    p = Path(path)
    if not p.is_file():
        raise ToolError("INPUT_NOT_FOUND", f"Input file not found: {p.name}")
    if p.suffix.lower() not in allowed_suffixes:
        raise ToolError(
            "INPUT_TYPE_INVALID", f"Expected one of {sorted(allowed_suffixes)}, got: {p.suffix or '(none)'}"
        )
    return p


def convert_to_pdf_with_libreoffice(input_path: Path, workspace: Path) -> Path:
    """Runs `soffice --headless --convert-to pdf` and returns the produced
    file's path. LibreOffice always names its output `<stem>.pdf`."""
    try:
        proc = subprocess.run(
            ["soffice", "--headless", "--norestore", "--convert-to", "pdf", "--outdir", str(workspace), str(input_path)],
            capture_output=True,
            text=True,
            timeout=SOFFICE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise ToolError(
            "OFFICE_ENGINE_NOT_FOUND", "LibreOffice (soffice) is not installed or not on PATH."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ToolError(
            "CONVERSION_TIMED_OUT", f"Conversion did not finish within {SOFFICE_TIMEOUT_SECONDS}s."
        ) from exc

    produced = workspace / f"{input_path.stem}.pdf"
    if proc.returncode != 0 or not produced.is_file():
        detail = proc.stderr.strip() or proc.stdout.strip() or "no output file was produced"
        raise ToolError("CONVERSION_FAILED", f"LibreOffice conversion failed: {detail}")

    return produced


def make_office_to_pdf_tool(allowed_suffixes: set[str]):
    """Builds a `JobRequest -> JobResult` tool function for one
    "<office format> -> PDF" conversion, sharing all validation and
    process-handling logic."""

    def _convert(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
        if len(request.inputs) != 1:
            raise ToolError("INVALID_INPUT", "This conversion requires exactly one input file.")

        input_path = require_input_office_file(request.inputs[0], allowed_suffixes)
        produced = convert_to_pdf_with_libreoffice(input_path, workspace)

        filename = output_filename(request.options, "outputFilename", f"{input_path.stem}.pdf")
        out_path = workspace / filename
        if produced != out_path:
            produced.rename(out_path)

        return [out_path], {}, [FORMAT_WARNING]

    def tool(request: JobRequest) -> JobResult:
        return run_tool(request, _convert)

    return tool
