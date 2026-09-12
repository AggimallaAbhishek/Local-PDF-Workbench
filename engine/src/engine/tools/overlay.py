"""Shared helper for tools that stamp a reportlab-drawn overlay onto every
page of an input PDF (watermark, page numbers): PLAN.md's "overlay pages
via reportlab, merged with pypdf".
"""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

# draw(canvas, page_width, page_height, page_number, page_count) -> None
DrawFn = Callable[[canvas.Canvas, float, float, int, int], None]


def stamp_pdf(reader: PdfReader, draw: DrawFn) -> PdfWriter:
    writer = PdfWriter()
    page_count = len(reader.pages)

    # Pages must belong to the writer before merge_page is called on them -
    # merging into a bare PdfReader page is deprecated in pypdf.
    for page in reader.pages:
        writer.add_page(page)

    for index, page in enumerate(writer.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=(width, height))
        draw(c, width, height, index, page_count)
        # A canvas with nothing drawn on it produces zero pages, not one
        # blank page - force the page through even when `draw` was a no-op
        # (e.g. this page wasn't in the target set).
        c.showPage()
        c.save()
        buf.seek(0)

        page.merge_page(PdfReader(buf).pages[0])

    return writer
