from __future__ import annotations

from PIL import Image

from engine.jobs.contract import JobRequest
from engine.tools.pdf_to_jpg import pdf_to_jpg


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="pdf-to-jpg", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_pdf_to_jpg_renders_one_image_per_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3)

    result = pdf_to_jpg(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert len(result.outputs) == 3
    for path in result.outputs:
        assert path.endswith(".jpg")
        with Image.open(path) as img:
            assert img.format == "JPEG"


def test_pdf_to_jpg_rejects_bad_dpi(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = pdf_to_jpg(_request(inputs=[doc], options={"dpi": 5}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_pdf_to_jpg_renders_only_requested_pages(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=5)

    result = pdf_to_jpg(_request(inputs=[doc], options={"pages": [2, 4]}, output_dir=output_dir))

    assert result.status == "success"
    assert len(result.outputs) == 2
    assert result.metadata["renderedPages"] == [2, 4]
