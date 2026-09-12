from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.scan_import import scan_import


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="scan-import", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_scan_import_combines_and_enhances_by_default(make_image, output_dir):
    a = make_image("a.jpg")
    b = make_image("b.jpg")

    result = scan_import(_request(inputs=[a, b], output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["pageCount"] == 2
    assert result.metadata["enhanced"] is True
    assert len(PdfReader(result.outputs[0]).pages) == 2


def test_scan_import_can_skip_enhancement(make_image, output_dir):
    a = make_image("a.jpg")

    result = scan_import(_request(inputs=[a], options={"enhance": False}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["enhanced"] is False


def test_scan_import_rejects_unsupported_file(tmp_path, output_dir):
    bogus = tmp_path / "notes.txt"
    bogus.write_text("hello")

    result = scan_import(_request(inputs=[str(bogus)], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INPUT_NOT_IMAGE"
