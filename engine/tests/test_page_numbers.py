from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.page_numbers import page_numbers


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="page-numbers", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_page_numbers_default_format(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3)

    result = page_numbers(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert len(PdfReader(result.outputs[0]).pages) == 3


def test_page_numbers_rejects_bad_position(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = page_numbers(_request(inputs=[doc], options={"position": "middle"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_page_numbers_rejects_bad_format_string(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = page_numbers(_request(inputs=[doc], options={"format": "{bogus}"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_page_numbers_respects_start_at(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    result = page_numbers(_request(
        inputs=[doc],
        options={"startAt": 5, "format": "{page}"},
        output_dir=output_dir,
    ))

    assert result.status == "success"
