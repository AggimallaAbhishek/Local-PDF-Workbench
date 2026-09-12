from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.watermark import watermark


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="watermark", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_watermark_stamps_all_pages_by_default(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3)

    result = watermark(_request(inputs=[doc], options={"text": "DRAFT"}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["stampedPages"] == [1, 2, 3]
    assert len(PdfReader(result.outputs[0]).pages) == 3


def test_watermark_requires_text(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = watermark(_request(inputs=[doc], options={}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_watermark_rejects_bad_opacity(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = watermark(_request(inputs=[doc], options={"text": "DRAFT", "opacity": 1.5}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_watermark_stamps_only_selected_pages(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=4)

    result = watermark(_request(
        inputs=[doc],
        options={"text": "DRAFT", "pages": [2, 4]},
        output_dir=output_dir,
    ))

    assert result.status == "success"
    assert result.metadata["stampedPages"] == [2, 4]
