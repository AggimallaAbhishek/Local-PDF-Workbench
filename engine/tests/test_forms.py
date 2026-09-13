from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from engine.jobs.contract import JobRequest
from engine.tools.forms import forms


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="forms", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def _make_form_pdf(tmp_path) -> str:
    path = tmp_path / "form.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    form = c.acroForm
    form.textfield(name="name", x=100, y=690, width=200, height=20)
    form.checkbox(name="subscribe", x=150, y=645, size=20, checked=False)
    # Without an explicit showPage(), reportlab can fail to resolve the
    # field-to-page back-reference at save() time (raises a "forward
    # reference to 'Page1' not resolved" KeyError) - same root cause as the
    # overlay-page bug fixed earlier in engine/tools/overlay.py.
    c.showPage()
    c.save()
    return str(path)


def test_forms_fills_text_and_checkbox_fields(tmp_path, output_dir):
    from pypdf import PdfReader

    form_pdf = _make_form_pdf(tmp_path)

    result = forms(_request(
        inputs=[form_pdf],
        options={"fields": {"name": "Ada Lovelace", "subscribe": "/Yes"}},
        output_dir=output_dir,
    ))

    assert result.status == "success"
    assert result.metadata["fieldsFilled"] == 2

    filled_fields = PdfReader(result.outputs[0]).get_fields()
    assert filled_fields["name"]["/V"] == "Ada Lovelace"
    assert filled_fields["subscribe"]["/V"] == "/Yes"


def test_forms_warns_on_unknown_field_names(tmp_path, output_dir):
    form_pdf = _make_form_pdf(tmp_path)

    result = forms(_request(
        inputs=[form_pdf],
        options={"fields": {"name": "Ada", "doesNotExist": "x"}},
        output_dir=output_dir,
    ))

    assert result.status == "success"
    assert result.metadata["fieldsFilled"] == 1
    assert result.warnings
    assert "doesNotExist" in result.warnings[0]


def test_forms_rejects_pdf_with_no_fields(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = forms(_request(inputs=[doc], options={"fields": {"a": "b"}}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "NO_FORM_FIELDS"


def test_forms_requires_non_empty_fields(tmp_path, output_dir):
    form_pdf = _make_form_pdf(tmp_path)

    result = forms(_request(inputs=[form_pdf], options={"fields": {}}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"
