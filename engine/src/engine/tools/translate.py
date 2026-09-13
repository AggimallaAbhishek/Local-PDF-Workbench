"""Translate: produce a local, offline translation of a PDF's text content.

Uses a small local LLM (engine/tools/llm.py) - never a cloud API. Long
documents are truncated to fit the model's context window; a truncation
always produces an explicit warning.

options:
  targetLanguage: str (required) - a language name, e.g. "Spanish", "French"
  pages: "all" | [1, 3] (default "all")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, resolve_pages, run_tool
from engine.tools.llm import generate, load_llm

MAX_INPUT_CHARS = 6000  # smaller than summarize's budget - translation output is comparably long to input


def _extract_text(reader: PdfReader, pages: set[int]) -> str:
    parts = [reader.pages[page_number - 1].extract_text() or "" for page_number in sorted(pages)]
    return "\n".join(parts).strip()


def _translate(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Translate requires exactly one input PDF.")

    target_language = request.options.get("targetLanguage")
    if not target_language or not str(target_language).strip():
        raise ToolError("INVALID_OPTIONS", "'targetLanguage' is required.")
    target_language = str(target_language).strip()

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)
    pages = resolve_pages(request.options.get("pages"), page_count)
    text = _extract_text(reader, pages)
    if not text:
        raise ToolError("NO_TEXT_FOUND", "No extractable text found on the selected pages.")

    warnings = []
    truncated = len(text) > MAX_INPUT_CHARS
    if truncated:
        text = text[:MAX_INPUT_CHARS]
        warnings.append(
            f"The document was too long for the local model's context window; only the first "
            f"~{MAX_INPUT_CHARS} characters were translated."
        )

    llm = load_llm()
    translation = generate(
        llm,
        system_prompt=(
            f"You are a precise translation assistant. Translate the given document text into "
            f"{target_language}. Respond with only the translation, no preamble or explanation."
        ),
        user_prompt=text,
        max_tokens=2000,
    )

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_translated", suffix=".txt")
    out_path = workspace / filename
    out_path.write_text(translation, encoding="utf-8")

    metadata = {"pageCount": page_count, "targetLanguage": target_language, "truncated": truncated}
    return [out_path], metadata, warnings


def translate(request: JobRequest) -> JobResult:
    return run_tool(request, _translate)
