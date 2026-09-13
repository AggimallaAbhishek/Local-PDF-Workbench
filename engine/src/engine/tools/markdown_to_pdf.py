"""Markdown to PDF: render a Markdown file as a formatted PDF.

Converts Markdown -> HTML (python-markdown) -> PDF (headless LibreOffice,
the same mechanism as html_to_pdf), since LibreOffice has no native
Markdown import.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import markdown

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, run_tool
from engine.tools.office_convert import convert_to_pdf_with_libreoffice

SUPPORTED_SUFFIXES = {".md", ".markdown"}


def _require_input_markdown(path: str) -> Path:
    p = Path(path)
    if not p.is_file():
        raise ToolError("INPUT_NOT_FOUND", f"Input file not found: {p.name}")
    if p.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ToolError("INPUT_TYPE_INVALID", f"Expected a .md file, got: {p.suffix or '(none)'}")
    return p


def _markdown_to_pdf(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Markdown to PDF requires exactly one input file.")

    md_path = _require_input_markdown(request.inputs[0])
    try:
        source = md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ToolError("INPUT_NOT_TEXT", f"Could not read {md_path.name} as UTF-8 text.") from exc

    body = markdown.markdown(source, extensions=["extra", "sane_lists"])
    html_document = f"<html><head><meta charset='utf-8'></head><body>{body}</body></html>"

    html_path = workspace / f"{md_path.stem}.html"
    html_path.write_text(html_document, encoding="utf-8")

    produced = convert_to_pdf_with_libreoffice(html_path, workspace)

    filename = output_filename(request.options, "outputFilename", f"{md_path.stem}.pdf")
    out_path = workspace / filename
    if produced != out_path:
        produced.rename(out_path)

    return [out_path], {}, []


def markdown_to_pdf(request: JobRequest) -> JobResult:
    return run_tool(request, _markdown_to_pdf)
