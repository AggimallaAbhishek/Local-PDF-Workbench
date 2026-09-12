from __future__ import annotations

from engine.jobs.contract import JobRequest
from engine.tools.compare import compare


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="compare", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_compare_reports_differing_and_identical_pages(make_text_pdf, output_dir):
    doc_a = make_text_pdf("a.pdf", ["same text", "different in A"])
    doc_b = make_text_pdf("b.pdf", ["same text", "different in B"])

    result = compare(_request(inputs=[doc_a, doc_b], output_dir=output_dir))

    assert result.status == "success"
    assert result.outputs[0].endswith(".html")
    assert result.metadata["pagesCompared"] == 2
    assert result.metadata["pagesWithDifferences"] == [2]

    # difflib.HtmlDiff renders spaces as &nbsp; and wraps the changed word in
    # a <span>, so check for the escaped form rather than the literal phrase.
    html = open(result.outputs[0], encoding="utf-8").read()
    assert "No Differences Found" in html  # page 1
    assert 'class="diff_chg">A</span>' in html  # page 2's changed word
    assert 'class="diff_chg">B</span>' in html


def test_compare_warns_on_page_count_mismatch(make_text_pdf, output_dir):
    doc_a = make_text_pdf("a.pdf", ["page one", "page two", "page three"])
    doc_b = make_text_pdf("b.pdf", ["page one"])

    result = compare(_request(inputs=[doc_a, doc_b], output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["pagesCompared"] == 1
    assert result.warnings


def test_compare_requires_exactly_two_inputs(make_text_pdf, output_dir):
    doc_a = make_text_pdf("a.pdf", ["hello"])

    result = compare(_request(inputs=[doc_a], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_INPUT"
