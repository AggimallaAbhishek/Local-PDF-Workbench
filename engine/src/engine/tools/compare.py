"""Compare: highlight text differences between two PDFs, page by page.

Extracts text per page from both documents and renders a single HTML report
(via difflib.HtmlDiff) with additions/removals highlighted side by side.
This is a text-content diff only - layout, images, and formatting
differences are not detected.
"""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, require_input_pdf, run_tool


def _page_lines(reader: PdfReader, page_number: int) -> list[str]:
    return reader.pages[page_number - 1].extract_text().splitlines()


def _build_report(page_diffs: list[tuple[int, list[str], list[str]]]) -> str:
    differ = difflib.HtmlDiff(wrapcolumn=100)

    boilerplate = differ.make_file([], [], "", "")
    style_start = boilerplate.index("<style")
    style_end = boilerplate.index("</style>") + len("</style>")
    style_block = boilerplate[style_start:style_end]

    if not page_diffs:
        body = "<p>No comparable pages.</p>"
    else:
        sections = []
        for page_number, lines_a, lines_b in page_diffs:
            table = differ.make_table(
                lines_a,
                lines_b,
                fromdesc=f"Page {page_number} - A",
                todesc=f"Page {page_number} - B",
                context=True,
                numlines=2,
            )
            sections.append(f"<h2>Page {page_number}</h2>\n{table}")
        body = "\n<hr/>\n".join(sections)

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>PDF Comparison</title>{style_block}</head>"
        f"<body>{body}</body></html>"
    )


def _compare(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 2:
        raise ToolError("INVALID_INPUT", "Compare requires exactly two input PDFs.")

    path_a = require_input_pdf(request.inputs[0])
    path_b = require_input_pdf(request.inputs[1])

    try:
        reader_a = PdfReader(str(path_a))
        reader_b = PdfReader(str(path_b))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read one of the input PDFs: {exc}") from exc

    count_a, count_b = len(reader_a.pages), len(reader_b.pages)
    compared_pages = min(count_a, count_b)

    page_diffs = []
    differing_pages = []
    for page_number in range(1, compared_pages + 1):
        lines_a = _page_lines(reader_a, page_number)
        lines_b = _page_lines(reader_b, page_number)
        page_diffs.append((page_number, lines_a, lines_b))
        if lines_a != lines_b:
            differing_pages.append(page_number)

    report_html = _build_report(page_diffs)
    out_path = workspace / "comparison_report.html"
    out_path.write_text(report_html, encoding="utf-8")

    warnings = []
    if count_a != count_b:
        longer = "A" if count_a > count_b else "B"
        warnings.append(
            f"Document {longer} has {abs(count_a - count_b)} extra page(s) not included in the comparison."
        )

    metadata = {
        "pageCountA": count_a,
        "pageCountB": count_b,
        "pagesCompared": compared_pages,
        "pagesWithDifferences": differing_pages,
    }
    return [out_path], metadata, warnings


def compare(request: JobRequest) -> JobResult:
    return run_tool(request, _compare)
