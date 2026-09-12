"""Shared plumbing every page-management tool uses.

Implements the processing sequence from PLAN.md §3: validate inputs ->
execute in a temp dir -> validate output -> atomically move to outputDir ->
report result -> clean up temp dir. Individual tools only implement the
"execute" step; this module handles the rest so every tool gets the same
input/output validation and error taxonomy for free.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from engine.jobs.contract import JobRequest, JobResult

ToolBody = Callable[[JobRequest, Path], tuple[list[Path], dict[str, Any], list[str]]]


class ToolError(Exception):
    """A structured, expected failure. Caught by `run_tool` and turned into
    a JobResult.failed(code, message) — never propagates as a raw traceback.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def require_input_pdf(path: str) -> Path:
    p = Path(path)
    if not p.is_file():
        raise ToolError("INPUT_NOT_FOUND", f"Input file not found: {p.name}")
    if p.suffix.lower() != ".pdf":
        raise ToolError("INPUT_NOT_PDF", f"Input is not a .pdf file: {p.name}")
    return p


def require_output_dir(path: str) -> Path:
    p = Path(path)
    if p.exists() and not p.is_dir():
        raise ToolError("OUTPUT_DIR_INVALID", f"Output path exists and is not a directory: {path}")
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ToolError("OUTPUT_DIR_NOT_CREATABLE", f"Could not create output directory: {exc}") from exc
    return p


def resolve_pages(raw_pages: Any, page_count: int) -> set[int]:
    """Parses the "pages": "all" | [1, 3] option shape shared by several
    tools (rotate, watermark, redact, crop) that act on a page subset."""
    if raw_pages in (None, "all"):
        return set(range(1, page_count + 1))
    if not isinstance(raw_pages, list) or not raw_pages:
        raise ToolError("INVALID_OPTIONS", "'pages' must be \"all\" or a non-empty list of page numbers.")

    pages = set()
    for entry in raw_pages:
        page_number = int(entry)
        if page_number < 1 or page_number > page_count:
            raise ToolError(
                "PAGE_OUT_OF_RANGE",
                f"Page {page_number} is out of range for a {page_count}-page document.",
            )
        pages.add(page_number)
    return pages


def output_filename(options: dict[str, Any], key: str, default: str) -> str:
    name = options.get(key) or default
    if not str(name).lower().endswith(".pdf"):
        name = f"{name}.pdf"
    return str(name)


@contextmanager
def temp_workspace():
    directory = tempfile.mkdtemp(prefix="lpw-job-")
    try:
        yield Path(directory)
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def _finalize_one(temp_path: Path, output_dir: Path, overwrite: bool) -> Path:
    if not temp_path.is_file() or temp_path.stat().st_size == 0:
        raise ToolError(
            "OUTPUT_VALIDATION_FAILED",
            f"Output file is missing or empty: {temp_path.name}",
        )

    target = output_dir / temp_path.name
    if target.exists() and not overwrite:
        stem, suffix = target.stem, target.suffix
        i = 1
        while target.exists():
            target = output_dir / f"{stem} ({i}){suffix}"
            i += 1

    shutil.move(str(temp_path), str(target))
    return target


def run_tool(request: JobRequest, body: ToolBody) -> JobResult:
    try:
        output_dir = require_output_dir(request.output_dir)
        with temp_workspace() as workspace:
            temp_outputs, metadata, warnings = body(request, workspace)
            if not temp_outputs:
                raise ToolError("NO_OUTPUT_PRODUCED", "Tool completed but produced no output file.")

            final_outputs = [
                _finalize_one(temp_path, output_dir, request.overwrite_original)
                for temp_path in temp_outputs
            ]

            return JobResult.ok(
                request.job_id,
                outputs=[str(p) for p in final_outputs],
                metadata=metadata,
                warnings=warnings,
            )
    except ToolError as exc:
        return JobResult.failed(request.job_id, exc.code, exc.message)
