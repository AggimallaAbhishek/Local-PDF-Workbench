"""Maps a job's `tool` name to its implementation."""

from __future__ import annotations

from collections.abc import Callable

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.compress import compress
from engine.tools.jpg_to_pdf import jpg_to_pdf
from engine.tools.merge import merge
from engine.tools.organize import organize
from engine.tools.page_numbers import page_numbers
from engine.tools.pdf_to_jpg import pdf_to_jpg
from engine.tools.preview import preview
from engine.tools.rotate import rotate
from engine.tools.split import split
from engine.tools.watermark import watermark

ToolHandler = Callable[[JobRequest], JobResult]

REGISTRY: dict[str, ToolHandler] = {
    "merge": merge,
    "split": split,
    "rotate": rotate,
    "organize": organize,
    "preview": preview,
    "compress": compress,
    "watermark": watermark,
    "page-numbers": page_numbers,
    "pdf-to-jpg": pdf_to_jpg,
    "jpg-to-pdf": jpg_to_pdf,
}


def get_handler(tool: str) -> ToolHandler | None:
    return REGISTRY.get(tool)
