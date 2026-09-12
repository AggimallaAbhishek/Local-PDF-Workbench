from __future__ import annotations

import pytest
from PIL import Image
from pypdf import PdfWriter
from reportlab.pdfgen import canvas


@pytest.fixture
def make_pdf(tmp_path):
    """Writes an N-page blank PDF and returns its path as a string."""

    def _make(name: str, pages: int, size: tuple[int, int] = (200, 300)) -> str:
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=size[0], height=size[1])
        path = tmp_path / name
        with path.open("wb") as f:
            writer.write(f)
        return str(path)

    return _make


@pytest.fixture
def output_dir(tmp_path):
    d = tmp_path / "out"
    d.mkdir()
    return str(d)


@pytest.fixture
def make_text_pdf(tmp_path):
    """Writes a PDF whose pages contain real drawn text (for tools that
    search or extract text, e.g. redact), one line per page."""

    def _make(name: str, pages_text: list[str], size: tuple[int, int] = (400, 400)) -> str:
        path = tmp_path / name
        c = canvas.Canvas(str(path), pagesize=size)
        for line in pages_text:
            c.setFont("Helvetica", 20)
            c.drawString(50, size[1] - 100, line)
            c.showPage()
        c.save()
        return str(path)

    return _make


@pytest.fixture
def make_image(tmp_path):
    """Writes a solid-color image and returns its path as a string."""

    def _make(name: str, size: tuple[int, int] = (100, 100), color=(200, 100, 50)) -> str:
        path = tmp_path / name
        Image.new("RGB", size, color).save(path)
        return str(path)

    return _make
