from __future__ import annotations

import pymupdf

from engine.jobs.contract import JobRequest
from engine.tools.ocr import ocr


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="ocr", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_ocr_adds_searchable_text_to_a_scan(make_scanned_pdf, output_dir):
    doc = make_scanned_pdf("scan.pdf", "Invoice Number 12345")

    before = pymupdf.open(doc)
    assert before[0].get_text().strip() == ""
    before.close()

    result = ocr(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["wordsRecognized"] > 0

    after = pymupdf.open(result.outputs[0])
    text = after[0].get_text()
    assert "Invoice" in text
    assert "12345" in text
    # the original scanned image must still be present - OCR only adds a
    # text layer, it never replaces the visible page content
    assert len(after[0].get_images()) == 1
    after.close()


def test_ocr_rejects_bad_dpi(make_scanned_pdf, output_dir):
    doc = make_scanned_pdf("scan.pdf", "hello")

    result = ocr(_request(inputs=[doc], options={"dpi": 50}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_ocr_only_processes_selected_pages(make_pdf, make_scanned_pdf, output_dir, tmp_path):
    from pypdf import PdfReader, PdfWriter

    scan_path = make_scanned_pdf("scan.pdf", "PageOneWord")
    scanned_page = PdfReader(scan_path).pages[0]
    blank_page_doc = PdfReader(make_pdf("blank.pdf", pages=1, size=(612, 792)))

    writer = PdfWriter()
    writer.add_page(scanned_page)
    writer.add_page(blank_page_doc.pages[0])
    combined = tmp_path / "combined.pdf"
    with combined.open("wb") as f:
        writer.write(f)

    result = ocr(_request(inputs=[str(combined)], options={"pages": [1]}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["ocrPages"] == [1]


def test_ocr_warns_when_nothing_recognized(make_pdf, output_dir):
    doc = make_pdf("blank.pdf", pages=1, size=(612, 792))

    result = ocr(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["wordsRecognized"] == 0
    assert result.warnings
