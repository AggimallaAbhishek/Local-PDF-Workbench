"""Redact: permanently remove every occurrence of a literal text string.

Uses PyMuPDF's redaction annotations, which strip the underlying text from
the page's content stream when applied - not just paint over it. Verified:
after redaction, the target text is absent from both extracted text and the
saved file's raw bytes (a plain black rectangle overlay would fail both).

options:
  text: str (required) - exact, case-sensitive text to find and redact
  pages: "all" | [1, 3] (default "all")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, resolve_pages, run_tool


def _redact(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Redact requires exactly one input PDF.")

    text = request.options.get("text")
    if not text:
        raise ToolError("INVALID_OPTIONS", "'text' is required.")

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        doc = pymupdf.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    try:
        page_count = doc.page_count
        target_pages = resolve_pages(request.options.get("pages"), page_count)

        occurrences = 0
        for page_number in target_pages:
            page = doc[page_number - 1]
            rects = page.search_for(text)
            if not rects:
                continue
            for rect in rects:
                page.add_redact_annot(rect, fill=(0, 0, 0))
            page.apply_redactions()
            occurrences += len(rects)

        filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_redacted.pdf")
        out_path = workspace / filename
        doc.save(str(out_path))
    finally:
        doc.close()

    warnings = []
    if occurrences == 0:
        warnings.append("No occurrences of the given text were found; nothing was redacted.")

    metadata = {"pageCount": page_count, "occurrencesRedacted": occurrences}
    return [out_path], metadata, warnings


def redact(request: JobRequest) -> JobResult:
    return run_tool(request, _redact)
