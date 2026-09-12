from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.rotate import rotate


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="rotate", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_rotate_specific_pages(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3)

    result = rotate(_request(inputs=[doc], options={"angle": 90, "pages": [2]}, output_dir=output_dir))

    assert result.status == "success"
    pages = PdfReader(result.outputs[0]).pages
    assert pages[0].rotation == 0
    assert pages[1].rotation == 90
    assert pages[2].rotation == 0


def test_rotate_all_pages_default(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    result = rotate(_request(inputs=[doc], options={"angle": 180}, output_dir=output_dir))

    assert result.status == "success"
    pages = PdfReader(result.outputs[0]).pages
    assert all(p.rotation == 180 for p in pages)


def test_rotate_rejects_invalid_angle(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = rotate(_request(inputs=[doc], options={"angle": 45}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"
