"""OCR: make scanned pages searchable.

Renders each target page to an image, runs Tesseract to recognize words and
their positions, then draws an invisible text layer over the *original*
page content at those positions (reportlab text render mode 3). The visible
page is untouched - only the ability to select/search/copy text is added.
Verified: a page with zero extractable text gets exactly the OCR'd words
back via an independent parser, with the original image still present.

options:
  language: str (default "eng") - a Tesseract language code
  pages: "all" | [1, 3] (default "all")
  dpi: int, 150-600 (default 300) - render resolution; higher improves
       OCR accuracy on small text at the cost of processing time
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pymupdf
import pytesseract
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas

from engine.tools.common import ToolError, output_filename, require_input_pdf, resolve_pages, run_tool
from engine.tools.overlay import stamp_pdf
from engine.jobs.contract import JobRequest, JobResult

DEFAULT_DPI = 300
MIN_CONFIDENCE = 0  # Tesseract confidence is 0-100, or -1 for structural (non-word) boxes


def _ocr_words(image: Image.Image, language: str) -> list[dict[str, Any]]:
    try:
        data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise ToolError(
            "OCR_ENGINE_NOT_FOUND",
            "Tesseract is not installed or not on PATH - OCR requires a local Tesseract install.",
        ) from exc
    except pytesseract.pytesseract.TesseractError as exc:
        raise ToolError("OCR_FAILED", f"Tesseract failed: {exc}") from exc

    words = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if not text or int(data["conf"][i]) < MIN_CONFIDENCE:
            continue
        words.append(
            {
                "text": text,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            }
        )
    return words


def _draw_invisible_words(c: canvas.Canvas, words: list[dict[str, Any]], px_per_pt: float, page_height_pt: float) -> None:
    for word in words:
        x_pt = word["left"] / px_per_pt
        y_pt = page_height_pt - (word["top"] + word["height"]) / px_per_pt
        font_size = max(word["height"] / px_per_pt, 1.0)

        text_width = c.stringWidth(word["text"], "Helvetica", font_size)
        target_width = word["width"] / px_per_pt
        h_scale = (target_width / text_width) if text_width > 0 else 1.0

        c.saveState()
        c.translate(x_pt, y_pt)
        c.scale(h_scale, 1)
        text_object = c.beginText(0, 0)
        text_object.setTextRenderMode(3)  # invisible: selectable/searchable, not painted
        text_object.setFont("Helvetica", font_size)
        text_object.textOut(word["text"])
        c.drawText(text_object)
        c.restoreState()


def _ocr(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "OCR requires exactly one input PDF.")

    dpi = int(request.options.get("dpi", DEFAULT_DPI))
    if not 150 <= dpi <= 600:
        raise ToolError("INVALID_OPTIONS", "'dpi' must be between 150 and 600.")
    language = str(request.options.get("language", "eng"))

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
        rendered_doc = pymupdf.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    try:
        page_count = len(reader.pages)
        target_pages = resolve_pages(request.options.get("pages"), page_count)
        zoom = dpi / 72.0
        px_per_pt = zoom

        words_by_page: dict[int, list[dict[str, Any]]] = {}
        for page_number in target_pages:
            pix = rendered_doc[page_number - 1].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            words_by_page[page_number] = _ocr_words(image, language)
    finally:
        rendered_doc.close()

    def draw(c: canvas.Canvas, _width: float, height: float, page_number: int, _total: int) -> None:
        _draw_invisible_words(c, words_by_page.get(page_number, []), px_per_pt, height)

    writer = stamp_pdf(reader, draw)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_ocr.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    word_count = sum(len(words) for words in words_by_page.values())
    warnings = []
    if word_count == 0:
        warnings.append("No text was recognized on the selected pages.")

    metadata = {"pageCount": page_count, "ocrPages": sorted(target_pages), "wordsRecognized": word_count}
    return [out_path], metadata, warnings


def ocr(request: JobRequest) -> JobResult:
    return run_tool(request, _ocr)
