from __future__ import annotations

import pymupdf

from engine.jobs.contract import JobRequest
from engine.tools.redact import redact


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="redact", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_redact_strips_matching_text_permanently(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["SECRET: 12345, keep this part"])

    result = redact(_request(inputs=[doc], options={"text": "SECRET: 12345"}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["occurrencesRedacted"] == 1

    out = pymupdf.open(result.outputs[0])
    text = out[0].get_text()
    out.close()
    assert "SECRET" not in text
    assert "12345" not in text
    assert "keep this part" in text

    raw = open(result.outputs[0], "rb").read()
    assert b"12345" not in raw


def test_redact_warns_when_text_not_found(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["nothing sensitive here"])

    result = redact(_request(inputs=[doc], options={"text": "NOPE"}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["occurrencesRedacted"] == 0
    assert result.warnings


def test_redact_requires_text_option(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["hello"])

    result = redact(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_redact_only_affects_selected_pages(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["SECRET on page 1", "SECRET on page 2"])

    result = redact(_request(inputs=[doc], options={"text": "SECRET", "pages": [1]}, output_dir=output_dir))

    assert result.status == "success"
    out = pymupdf.open(result.outputs[0])
    assert "SECRET" not in out[0].get_text()
    assert "SECRET" in out[1].get_text()
    out.close()
