from __future__ import annotations

import re

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.repair import repair


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="repair", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def _corrupt_xref_offset(path: str) -> None:
    """Simulates a common real-world corruption: a stale/broken startxref
    offset, while every object is still intact in the file body."""
    data = bytearray(open(path, "rb").read())
    start = data.find(b"startxref")
    end = data.find(b"%%EOF", start)
    segment = bytes(data[start:end])
    corrupted = re.sub(rb"\d+", b"999999", segment, count=1)
    data[start:end] = corrupted
    with open(path, "wb") as f:
        f.write(data)


def test_repair_recovers_broken_xref_table(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3)
    _corrupt_xref_offset(doc)

    result = repair(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert len(PdfReader(result.outputs[0]).pages) == 3


def test_repair_reports_unrepairable_garbage(tmp_path, output_dir):
    garbage = tmp_path / "garbage.pdf"
    garbage.write_bytes(b"not a pdf at all" * 20)

    result = repair(_request(inputs=[str(garbage)], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "UNREPAIRABLE"


def test_repair_passes_through_a_healthy_pdf(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    result = repair(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "success"
    assert len(PdfReader(result.outputs[0]).pages) == 2
