"""Tests for the shared tool plumbing in engine.tools.common."""

from __future__ import annotations

import os
from pathlib import Path

from engine.jobs.contract import JobRequest
from engine.tools.common import run_tool


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="test", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def _write_one_file(request: JobRequest, workspace: Path):
    out = workspace / "output.txt"
    out.write_text("hello")
    return [out], {}, []


def test_finalize_only_ever_renames_within_the_same_directory(output_dir, monkeypatch):
    """PLAN.md §3 requires the temp-dir output be "atomically move[d]" into
    outputDir. os.rename/os.replace are only atomic when source and
    destination share a directory (hence a filesystem) - a rename whose
    source lives elsewhere (e.g. the temp workspace, while outputDir is on
    an external drive) either raises EXDEV or - via shutil.move's fallback -
    silently degrades to a non-atomic copy+unlink. So the only way to keep
    the "atomic move" promise for an arbitrary outputDir is to stage the
    file inside outputDir's own filesystem first and finish with a
    same-directory rename. This test asserts that invariant directly rather
    than relying on triggering a real EXDEV, which isn't reproducible
    without two real filesystems.
    """
    calls: list[tuple[str, str]] = []
    real_rename = os.rename
    real_replace = os.replace

    def spy_rename(src, dst, *a, **kw):
        calls.append((str(src), str(dst)))
        return real_rename(src, dst, *a, **kw)

    def spy_replace(src, dst, *a, **kw):
        calls.append((str(src), str(dst)))
        return real_replace(src, dst, *a, **kw)

    monkeypatch.setattr(os, "rename", spy_rename)
    monkeypatch.setattr(os, "replace", spy_replace)

    result = run_tool(_request(output_dir=output_dir), _write_one_file)

    assert result.status == "success"
    assert calls, "expected finalize to move the file via os.rename/os.replace"
    for src, dst in calls:
        assert os.path.dirname(src) == os.path.dirname(dst), (
            f"rename/replace crossed directories ({src} -> {dst}); this is only atomic "
            "when the file was already staged inside outputDir's own filesystem"
        )


def test_finalize_leaves_no_staging_artifacts(output_dir):
    result = run_tool(_request(output_dir=output_dir), _write_one_file)

    assert result.status == "success"
    leftovers = [p for p in Path(output_dir).iterdir() if p.name.startswith(".tmp")]
    assert leftovers == []


def test_finalize_produces_correct_content(output_dir):
    result = run_tool(_request(output_dir=output_dir), _write_one_file)

    assert result.status == "success"
    assert Path(result.outputs[0]).read_text() == "hello"


def test_finalize_rejects_a_structurally_broken_pdf(output_dir):
    """PLAN.md §9/§11: every success path must validate output by
    re-opening it with an independent parser, not just check it's
    non-empty. A tool bug that writes garbage bytes with a .pdf name is
    exactly what that check exists to catch.
    """

    def write_garbage_pdf(request: JobRequest, workspace: Path):
        out = workspace / "broken.pdf"
        out.write_bytes(b"not actually a pdf, just bytes with a .pdf name")
        return [out], {}, []

    result = run_tool(_request(output_dir=output_dir), write_garbage_pdf)

    assert result.status == "error"
    assert result.error.code == "OUTPUT_VALIDATION_FAILED"


def test_finalize_accepts_an_encrypted_pdf(make_pdf, output_dir):
    """An encrypted output (e.g. from the `protect` tool) can't have its
    pages read without the password - validation must not require that.
    """
    from pypdf import PdfReader, PdfWriter

    def write_encrypted_pdf(request: JobRequest, workspace: Path):
        source = PdfReader(make_pdf("doc.pdf", pages=1))
        writer = PdfWriter()
        for page in source.pages:
            writer.add_page(page)
        writer.encrypt(user_password="hunter2")
        out = workspace / "doc.pdf"
        with out.open("wb") as f:
            writer.write(f)
        return [out], {}, []

    result = run_tool(_request(output_dir=output_dir), write_encrypted_pdf)

    assert result.status == "success"
    assert PdfReader(result.outputs[0]).is_encrypted


def test_finalize_accepts_a_real_pdf(make_pdf, output_dir):
    def write_real_pdf(request: JobRequest, workspace: Path):
        source = Path(make_pdf("doc.pdf", pages=1))
        out = workspace / "doc.pdf"
        out.write_bytes(source.read_bytes())
        return [out], {}, []

    result = run_tool(_request(output_dir=output_dir), write_real_pdf)

    assert result.status == "success"
