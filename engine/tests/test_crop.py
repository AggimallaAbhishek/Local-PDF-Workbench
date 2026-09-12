from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.crop import crop


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="crop", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_crop_shrinks_page_box(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1, size=(200, 300))

    result = crop(_request(inputs=[doc], options={"margins": {"top": 10, "bottom": 10, "left": 20, "right": 20}}, output_dir=output_dir))

    assert result.status == "success"
    page = PdfReader(result.outputs[0]).pages[0]
    assert float(page.mediabox.width) == 160
    assert float(page.mediabox.height) == 280


def test_crop_rejects_margins_that_consume_whole_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1, size=(100, 100))

    result = crop(_request(inputs=[doc], options={"margins": {"left": 60, "right": 60}}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "MARGINS_TOO_LARGE"


def test_crop_rejects_negative_margin(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = crop(_request(inputs=[doc], options={"margins": {"top": -5}}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"
