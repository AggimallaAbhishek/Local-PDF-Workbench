"""Fill Forms: fill a PDF's AcroForm fields and export the result.

options:
  fields: a non-empty object mapping field name -> value. Text fields take
          a string; checkboxes/radio buttons take one of their state names
          (e.g. "/Yes" or "/Off" - see the field's own definition).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfWriter

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool


def _fill_forms(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Fill Forms requires exactly one input PDF.")

    fields = request.options.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise ToolError("INVALID_OPTIONS", "'fields' must be a non-empty object of field name -> value.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        writer = PdfWriter(clone_from=str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    existing_fields = writer.get_fields() or {}
    if not existing_fields:
        raise ToolError("NO_FORM_FIELDS", f"{pdf_path.name} has no fillable form fields.")

    unknown = sorted(set(fields) - set(existing_fields))
    known_values = {name: value for name, value in fields.items() if name not in unknown}

    for page in writer.pages:
        writer.update_page_form_field_values(page, known_values)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_filled.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    warnings = []
    if unknown:
        warnings.append(f"These field names were not found in the form and were skipped: {unknown}")

    metadata = {"fieldsFilled": len(known_values), "availableFields": sorted(existing_fields)}
    return [out_path], metadata, warnings


def forms(request: JobRequest) -> JobResult:
    return run_tool(request, _fill_forms)
