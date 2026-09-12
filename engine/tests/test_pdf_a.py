from __future__ import annotations

import pikepdf

from engine.jobs.contract import JobRequest
from engine.tools.pdf_a import pdf_a


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="pdf-a", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_pdf_a_embeds_output_intent_and_metadata(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = pdf_a(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["conformance"] == "PDF/A-2B"
    assert result.warnings, "must always warn that this is best-effort, not validated"

    out = pikepdf.open(result.outputs[0])
    assert len(out.Root.OutputIntents) == 1
    with out.open_metadata() as meta:
        assert meta.get("pdfaid:part") == "2"
        assert meta.get("pdfaid:conformance") == "B"
    out.close()


def test_pdf_a_rejects_invalid_conformance(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = pdf_a(_request(inputs=[doc], options={"conformance": "9Z"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_pdf_a_accepts_alternate_conformance_level(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = pdf_a(_request(inputs=[doc], options={"conformance": "1B"}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["conformance"] == "PDF/A-1B"
