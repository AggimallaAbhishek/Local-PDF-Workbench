from __future__ import annotations

import shutil

import pytest
from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.markdown_to_pdf import markdown_to_pdf

pytestmark = pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice (soffice) not installed")


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="markdown", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_markdown_renders_headings_and_lists(tmp_path, output_dir):
    md_path = tmp_path / "doc.md"
    md_path.write_text("# Title\n\nSome **bold** text.\n\n- one\n- two\n", encoding="utf-8")

    result = markdown_to_pdf(_request(inputs=[str(md_path)], output_dir=output_dir))

    assert result.status == "success"
    text = PdfReader(result.outputs[0]).pages[0].extract_text()
    assert "Title" in text
    assert "bold" in text
    assert "one" in text


def test_markdown_rejects_wrong_extension(tmp_path, output_dir):
    bogus = tmp_path / "notes.txt"
    bogus.write_text("hello")

    result = markdown_to_pdf(_request(inputs=[str(bogus)], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INPUT_TYPE_INVALID"
