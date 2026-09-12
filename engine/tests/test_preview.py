from __future__ import annotations

from engine.jobs.contract import JobRequest
from engine.tools.preview import preview


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="preview", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_preview_renders_one_thumbnail_per_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3)

    result = preview(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert len(result.outputs) == 3
    assert all(path.endswith(".png") for path in result.outputs)
    assert result.metadata["pageCount"] == 3


def test_preview_renders_only_requested_pages(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=5)

    result = preview(_request(inputs=[doc], options={"pages": [2, 4]}, output_dir=output_dir))

    assert result.status == "success"
    assert len(result.outputs) == 2
    assert result.metadata["renderedPages"] == [2, 4]


def test_preview_rejects_out_of_range_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    result = preview(_request(inputs=[doc], options={"pages": [9]}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "PAGE_OUT_OF_RANGE"
