from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.merge import merge


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="merge", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_merge_combines_pages_in_order(make_pdf, output_dir):
    a = make_pdf("a.pdf", pages=2)
    b = make_pdf("b.pdf", pages=3)

    result = merge(_request(inputs=[a, b], output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["pageCount"] == 5
    assert len(result.outputs) == 1
    assert PdfReader(result.outputs[0]).pages.__len__() == 5


def test_merge_requires_two_inputs(make_pdf, output_dir):
    a = make_pdf("a.pdf", pages=1)

    result = merge(_request(inputs=[a], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_INPUT"


def test_merge_rejects_missing_input(output_dir):
    result = merge(_request(inputs=["/no/such/a.pdf", "/no/such/b.pdf"], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INPUT_NOT_FOUND"


def test_merge_creates_missing_output_dir(make_pdf, tmp_path):
    a = make_pdf("a.pdf", pages=1)
    b = make_pdf("b.pdf", pages=1)
    missing_dir = str(tmp_path / "does" / "not" / "exist")

    result = merge(_request(inputs=[a, b], output_dir=missing_dir))

    assert result.status == "success"
    assert result.outputs[0].startswith(missing_dir)
