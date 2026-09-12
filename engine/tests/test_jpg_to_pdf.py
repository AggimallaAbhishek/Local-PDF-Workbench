from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.jpg_to_pdf import jpg_to_pdf


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="jpg-to-pdf", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_jpg_to_pdf_combines_images_in_order(make_image, output_dir):
    a = make_image("a.jpg")
    b = make_image("b.png")

    result = jpg_to_pdf(_request(inputs=[a, b], output_dir=output_dir))

    assert result.status == "success"
    assert len(PdfReader(result.outputs[0]).pages) == 2


def test_jpg_to_pdf_rejects_unsupported_extension(tmp_path, output_dir):
    bogus = tmp_path / "notes.txt"
    bogus.write_text("hello")

    result = jpg_to_pdf(_request(inputs=[str(bogus)], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INPUT_NOT_IMAGE"


def test_jpg_to_pdf_requires_at_least_one_input(output_dir):
    result = jpg_to_pdf(_request(inputs=[], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_INPUT"
