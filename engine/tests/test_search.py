from __future__ import annotations

from engine.jobs.contract import JobRequest
from engine.tools.search import search


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="search", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_search_finds_matches_across_files_and_pages(make_text_pdf, output_dir):
    doc_a = make_text_pdf("a.pdf", ["The quick brown fox", "nothing here"])
    doc_b = make_text_pdf("b.pdf", ["another fox sighting"])

    result = search(_request(inputs=[doc_a, doc_b], options={"query": "fox"}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["matchCount"] == 2
    assert result.metadata["filesScanned"] == 2
    pages = sorted((m["file"], m["page"]) for m in result.metadata["matches"])
    assert pages == [("a.pdf", 1), ("b.pdf", 1)]
    assert result.outputs[0].endswith(".html")


def test_search_is_case_insensitive_by_default(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["The Quick Brown FOX"])

    result = search(_request(inputs=[doc], options={"query": "fox"}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["matchCount"] == 1


def test_search_case_sensitive_option(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["The Quick Brown FOX"])

    result = search(_request(
        inputs=[doc],
        options={"query": "fox", "caseSensitive": True},
        output_dir=output_dir,
    ))

    assert result.status == "success"
    assert result.metadata["matchCount"] == 0


def test_search_skips_unreadable_files_with_warning(make_text_pdf, tmp_path, output_dir):
    doc = make_text_pdf("doc.pdf", ["fox found here"])
    bogus = tmp_path / "bogus.pdf"
    bogus.write_bytes(b"not a pdf")

    result = search(_request(inputs=[doc, str(bogus)], options={"query": "fox"}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["matchCount"] == 1
    assert result.metadata["filesSkipped"] == ["bogus.pdf"]
    assert result.warnings


def test_search_requires_query(make_text_pdf, output_dir):
    doc = make_text_pdf("doc.pdf", ["hello"])

    result = search(_request(inputs=[doc], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_search_requires_at_least_one_input(output_dir):
    result = search(_request(inputs=[], options={"query": "x"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_INPUT"
