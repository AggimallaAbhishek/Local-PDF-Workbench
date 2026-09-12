from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.compress import compress


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="compress", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_compress_produces_valid_pdf(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    result = compress(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert len(PdfReader(result.outputs[0]).pages) == 2
    assert "originalSizeBytes" in result.metadata
    assert "compressedSizeBytes" in result.metadata


def test_compress_rejects_invalid_quality(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = compress(_request(inputs=[doc], options={"quality": "ultra"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_compress_rejects_multiple_inputs(make_pdf, output_dir):
    a = make_pdf("a.pdf", pages=1)
    b = make_pdf("b.pdf", pages=1)

    result = compress(_request(inputs=[a, b], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_INPUT"
