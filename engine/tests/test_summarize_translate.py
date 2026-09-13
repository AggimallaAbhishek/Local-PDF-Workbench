"""Tests for summarize/translate. Real inference (~12s model load, the
first time within a test run) rather than mocked - a mock would only prove
the plumbing works, not that the actual local-AI path produces something
usable. Skipped entirely if the model file isn't present, since it's a
~1GB download not fetched automatically (see README)."""

from __future__ import annotations

import pytest

from engine.jobs.contract import JobRequest
from engine.tools.llm import model_path
from engine.tools.summarize import summarize
from engine.tools.translate import translate

pytestmark = pytest.mark.skipif(not model_path().is_file(), reason="local LLM model not downloaded")


def _request(tool: str, **overrides) -> JobRequest:
    base = dict(job_id="job-1", tool=tool, inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_summarize_produces_a_shorter_coherent_summary(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", [
        "Quarterly revenue grew twelve percent year over year, driven by the cloud services division. "
        "Operating costs rose slightly due to expanded engineering headcount. Growth is expected to continue."
    ])

    result = summarize(_request("summarize", inputs=[doc], options={"maxWords": 30}, output_dir=output_dir))

    assert result.status == "success"
    assert result.outputs[0].endswith(".txt")
    summary_text = open(result.outputs[0], encoding="utf-8").read()
    assert len(summary_text) > 0
    assert len(summary_text) < 600  # meaningfully shorter than a padded/looping failure would produce


def test_summarize_rejects_bad_max_words(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["hello"])

    result = summarize(_request("summarize", inputs=[doc], options={"maxWords": 5}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_summarize_rejects_pdf_with_no_text(make_pdf, output_dir):
    doc = make_pdf("blank.pdf", pages=1)

    result = summarize(_request("summarize", inputs=[doc], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "NO_TEXT_FOUND"


def test_translate_produces_target_language_text(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["The quick brown fox jumps over the lazy dog."])

    result = translate(_request(
        "translate", inputs=[doc], options={"targetLanguage": "Spanish"}, output_dir=output_dir,
    ))

    assert result.status == "success"
    assert result.metadata["targetLanguage"] == "Spanish"
    translated_text = open(result.outputs[0], encoding="utf-8").read()
    # a real Spanish translation should contain at least one common Spanish word/accent
    assert any(word in translated_text.lower() for word in ("el ", "la ", "zorro", "perro"))


def test_translate_requires_target_language(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["hello"])

    result = translate(_request("translate", inputs=[doc], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"
