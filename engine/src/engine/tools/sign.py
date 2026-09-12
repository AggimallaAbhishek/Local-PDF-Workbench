"""Sign: place a signature image onto one page.

Visual placement only - this stamps an image into the page content, it does
not add a cryptographic digital signature (that needs a certificate and is
out of scope here).

options:
  imagePath: str (required) - a signature image, ideally a PNG with a
             transparent background
  page: int (default: last page)
  x, y: float (default 50, 50) - bottom-left corner position, in points
  width: float (default 150) - rendered width in points; height follows
         the image's own aspect ratio
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool


def _sign(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Sign requires exactly one input PDF.")

    image_path_raw = request.options.get("imagePath")
    if not image_path_raw:
        raise ToolError("INVALID_OPTIONS", "'imagePath' is required.")
    image_path = Path(image_path_raw)
    if not image_path.is_file():
        raise ToolError("SIGNATURE_IMAGE_NOT_FOUND", f"Signature image not found: {image_path.name}")

    try:
        with Image.open(image_path) as img:
            img_width, img_height = img.size
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_IMAGE", f"Could not read signature image: {exc}") from exc

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    page_count = len(reader.pages)
    page_number = int(request.options.get("page", page_count))
    if page_number < 1 or page_number > page_count:
        raise ToolError("PAGE_OUT_OF_RANGE", f"Page {page_number} is out of range for a {page_count}-page document.")

    width = float(request.options.get("width", 150))
    if width <= 0:
        raise ToolError("INVALID_OPTIONS", "'width' must be positive.")
    height = width * (img_height / img_width)

    x = float(request.options.get("x", 50))
    y = float(request.options.get("y", 50))

    target_page = reader.pages[page_number - 1]
    page_width = float(target_page.mediabox.width)
    page_height = float(target_page.mediabox.height)
    if x < 0 or y < 0 or x + width > page_width or y + height > page_height:
        raise ToolError("SIGNATURE_OUT_OF_BOUNDS", "The signature placement falls outside the page.")

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))
    c.drawImage(str(image_path), x, y, width=width, height=height, mask="auto")
    c.showPage()
    c.save()
    buf.seek(0)
    overlay_page = PdfReader(buf).pages[0]

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.pages[page_number - 1].merge_page(overlay_page)

    filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_signed.pdf")
    out_path = workspace / filename
    with out_path.open("wb") as f:
        writer.write(f)

    metadata = {"pageCount": page_count, "signedPage": page_number}
    return [out_path], metadata, []


def sign(request: JobRequest) -> JobResult:
    return run_tool(request, _sign)
