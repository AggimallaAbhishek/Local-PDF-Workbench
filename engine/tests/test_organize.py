from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.organize import organize


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="organize", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_organize_reorders_pages(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3, size=(200, 300))

    result = organize(_request(inputs=[doc], options={"pageOrder": [3, 1, 2]}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["outputPageCount"] == 3
    assert len(PdfReader(result.outputs[0]).pages) == 3


def test_organize_drops_omitted_pages_with_warning(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=4)

    result = organize(_request(inputs=[doc], options={"pageOrder": [1, 3]}, output_dir=output_dir))

    assert result.status == "success"
    assert len(PdfReader(result.outputs[0]).pages) == 2
    assert result.warnings, "expected a warning noting dropped pages"


def test_organize_rejects_out_of_range_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    result = organize(_request(inputs=[doc], options={"pageOrder": [1, 9]}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "PAGE_OUT_OF_RANGE"
