"""Summarize: produce a local, offline summary of a PDF's text content.

Uses a small local LLM (engine/tools/llm.py) - never a cloud API. Long
documents are truncated to fit the model's context window; a truncation
always produces an explicit warning rather than silently summarizing only
part of the document.

options:
  maxWords: int, 20-1000 (default 150) - rough target length
  pages: "all" | [1, 3] (default "all")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, resolve_pages, run_tool
from engine.tools.llm import generate, load_llm

MAX_INPUT_CHARS = 8000  # leaves headroom in a 4096-token context for prompt + response


def _extract_text(reader: PdfReader, pages: set[int]) -> str:
    parts = [reader.pages[page_number - 1].extract_text() or "" for page_number in sorted(pages)]
    return "\n".join(parts).strip()


def _summarize(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Summarize requires exactly one input PDF.")

    max_words = int(request.options.get("maxWords", 150))
    if not 20 <= max_words <= 1000:
        raise ToolError("INVALID_OPTIONS", "'maxWords' must be between 20 and 1000.")

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
            f"~{MAX_INPUT_CHARS} characters were summarized."
        )

    llm = load_llm()
    summary = generate(
        llm,
        system_prompt=(
            f"You are a precise summarization assistant. Summarize the given document text in "
            f"about {max_words} words. Respond with only the summary, no preamble."
        ),
        user_prompt=text,
        max_tokens=max_words * 2,
    )

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_summary", suffix=".txt")
    out_path = workspace / filename
    out_path.write_text(summary, encoding="utf-8")

    metadata = {"pageCount": page_count, "wordCountApprox": len(summary.split()), "truncated": truncated}
    return [out_path], metadata, warnings


def summarize(request: JobRequest) -> JobResult:
    return run_tool(request, _summarize)
