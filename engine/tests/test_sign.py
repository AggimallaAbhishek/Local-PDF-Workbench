from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.sign import sign


def _request(**overrides) -> JobRequest:
    base = dict(job_id="job-1", tool="sign", inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def _make_signature_png(tmp_path) -> str:
    from PIL import Image

    path = tmp_path / "sig.png"
    Image.new("RGBA", (300, 100), (0, 0, 150, 200)).save(path)
    return str(path)


def test_sign_places_image_on_last_page_by_default(make_pdf, make_image, tmp_path, output_dir):
    doc = make_pdf("doc.pdf", pages=3, size=(400, 400))
    sig = _make_signature_png(tmp_path)

    result = sign(_request(inputs=[doc], options={"imagePath": sig}, output_dir=output_dir))

    assert result.status == "success"
    assert result.metadata["signedPage"] == 3
    assert len(PdfReader(result.outputs[0]).pages) == 3


def test_sign_rejects_missing_image(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = sign(_request(inputs=[doc], options={"imagePath": "/no/such/sig.png"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "SIGNATURE_IMAGE_NOT_FOUND"


def test_sign_rejects_out_of_bounds_placement(make_pdf, tmp_path, output_dir):
    doc = make_pdf("doc.pdf", pages=1, size=(100, 100))
    sig = _make_signature_png(tmp_path)

    result = sign(_request(
        inputs=[doc],
        options={"imagePath": sig, "x": 90, "y": 90, "width": 150},
        output_dir=output_dir,
    ))

    assert result.status == "error"
    assert result.error.code == "SIGNATURE_OUT_OF_BOUNDS"


def test_sign_rejects_page_out_of_range(make_pdf, tmp_path, output_dir):
    doc = make_pdf("doc.pdf", pages=2)
    sig = _make_signature_png(tmp_path)

    result = sign(_request(inputs=[doc], options={"imagePath": sig, "page": 5}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "PAGE_OUT_OF_RANGE"
