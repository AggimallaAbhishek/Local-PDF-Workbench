from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.annotate import annotate


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="annotate", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_annotate_draws_each_type_on_its_own_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=3, size=(400, 400))

    result = annotate(_request(
        inputs=[doc],
        options={
            "annotations": [
                {"type": "text", "page": 1, "x": 50, "y": 300, "text": "Hello", "color": "#ff0000"},
                {"type": "rectangle", "page": 2, "x": 20, "y": 20, "width": 100, "height": 50},
                {"type": "line", "page": 3, "x1": 0, "y1": 0, "x2": 400, "y2": 400},
            ],
        },
        output_dir=output_dir,
    ))

    assert result.status == "success"
    assert result.metadata["annotationCount"] == 3
    assert len(PdfReader(result.outputs[0]).pages) == 3


def test_annotate_requires_non_empty_list(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = annotate(_request(inputs=[doc], options={"annotations": []}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_annotate_rejects_unknown_type(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = annotate(_request(
        inputs=[doc],
        options={"annotations": [{"type": "circle", "page": 1, "x": 0, "y": 0}]},
        output_dir=output_dir,
    ))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_annotate_rejects_page_out_of_range(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = annotate(_request(
        inputs=[doc],
        options={"annotations": [{"type": "text", "page": 5, "x": 0, "y": 0, "text": "hi"}]},
        output_dir=output_dir,
    ))

    assert result.status == "error"
    assert result.error.code == "PAGE_OUT_OF_RANGE"


def test_annotate_rejects_missing_numeric_field(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = annotate(_request(
        inputs=[doc],
        options={"annotations": [{"type": "rectangle", "page": 1, "x": 0, "y": 0, "width": 10}]},
        output_dir=output_dir,
    ))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_annotate_rejects_empty_text(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = annotate(_request(
        inputs=[doc],
        options={"annotations": [{"type": "text", "page": 1, "x": 0, "y": 0, "text": "   "}]},
        output_dir=output_dir,
    ))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_annotate_rejects_invalid_color(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = annotate(_request(
        inputs=[doc],
        options={"annotations": [{"type": "text", "page": 1, "x": 0, "y": 0, "text": "hi", "color": "nope"}]},
        output_dir=output_dir,
    ))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_annotate_multiple_annotations_on_same_page(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1, size=(400, 400))

    result = annotate(_request(
        inputs=[doc],
        options={
            "annotations": [
                {"type": "text", "page": 1, "x": 10, "y": 10, "text": "one"},
                {"type": "text", "page": 1, "x": 10, "y": 30, "text": "two"},
            ],
        },
        output_dir=output_dir,
    ))

    assert result.status == "success"
    assert result.metadata["annotationCount"] == 2
