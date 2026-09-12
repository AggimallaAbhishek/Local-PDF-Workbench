from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.split import split


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="split", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_split_every_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3)

    result = split(_request(inputs=[doc], options={"mode": "everyPage"}, output_dir=output_dir))

    assert result.status == "success"
    assert len(result.outputs) == 3
    for out in result.outputs:
        assert len(PdfReader(out).pages) == 1


def test_split_by_ranges(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=6)

    result = split(_request(
        inputs=[doc],
        options={"mode": "ranges", "ranges": [[1, 2], [3, 6]]},
        output_dir=output_dir,
    ))

    assert result.status == "success"
    assert len(result.outputs) == 2
    page_counts = sorted(len(PdfReader(out).pages) for out in result.outputs)
    assert page_counts == [2, 4]


def test_split_rejects_out_of_range(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    result = split(_request(
        inputs=[doc],
        options={"mode": "ranges", "ranges": [[1, 5]]},
        output_dir=output_dir,
    ))

    assert result.status == "error"
    assert result.error.code == "PAGE_OUT_OF_RANGE"
