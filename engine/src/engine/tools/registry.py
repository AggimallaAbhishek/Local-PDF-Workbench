"""Maps a job's `tool` name to its implementation."""

from __future__ import annotations

from collections.abc import Callable

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.annotate import annotate
from engine.tools.compare import compare
from engine.tools.compress import compress
from engine.tools.crop import crop
from engine.tools.excel_to_pdf import excel_to_pdf
from engine.tools.forms import forms
from engine.tools.html_to_pdf import html_to_pdf
from engine.tools.jpg_to_pdf import jpg_to_pdf
from engine.tools.markdown_to_pdf import markdown_to_pdf
from engine.tools.merge import merge
from engine.tools.ocr import ocr
from engine.tools.organize import organize
from engine.tools.page_numbers import page_numbers
from engine.tools.pdf_a import pdf_a
from engine.tools.pdf_to_jpg import pdf_to_jpg
from engine.tools.ppt_to_pdf import ppt_to_pdf
from engine.tools.preview import preview
from engine.tools.protect import protect
from engine.tools.redact import redact
from engine.tools.repair import repair
from engine.tools.rotate import rotate
from engine.tools.scan_import import scan_import
from engine.tools.search import search
from engine.tools.sign import sign
from engine.tools.split import split
from engine.tools.unlock import unlock
from engine.tools.watermark import watermark
from engine.tools.word_to_pdf import word_to_pdf

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
    "crop": crop,
    "protect": protect,
    "unlock": unlock,
    "repair": repair,
    "redact": redact,
    "sign": sign,
    "compare": compare,
    "pdf-a": pdf_a,
    "scan-import": scan_import,
    "annotate": annotate,
    "ocr": ocr,
    "word-to-pdf": word_to_pdf,
    "excel-to-pdf": excel_to_pdf,
    "ppt-to-pdf": ppt_to_pdf,
    "html-to-pdf": html_to_pdf,
    "markdown": markdown_to_pdf,
    "forms": forms,
    "search": search,
}


def get_handler(tool: str) -> ToolHandler | None:
    return REGISTRY.get(tool)
