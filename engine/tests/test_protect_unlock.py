from __future__ import annotations

from pypdf import PdfReader

from engine.jobs.contract import JobRequest
from engine.tools.protect import protect
from engine.tools.unlock import unlock


def _request(tool: str, **overrides) -> JobRequest:
    base = dict(job_id="job-1", tool=tool, inputs=[], options={}, output_dir="/tmp", overwrite_original=False)
    base.update(overrides)
    return JobRequest(**base)


def test_protect_encrypts_and_unlock_reverses_it(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=2)

    protected = protect(_request("protect", inputs=[doc], options={"password": "hunter2"}, output_dir=output_dir))
    assert protected.status == "success"

    protected_path = protected.outputs[0]
    reader = PdfReader(protected_path)
    assert reader.is_encrypted

    unlocked = unlock(_request("unlock", inputs=[protected_path], options={"password": "hunter2"}, output_dir=output_dir))
    assert unlocked.status == "success"
    unlocked_reader = PdfReader(unlocked.outputs[0])
    assert not unlocked_reader.is_encrypted
    assert len(unlocked_reader.pages) == 2


def test_protect_requires_password(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = protect(_request("protect", inputs=[doc], output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "INVALID_OPTIONS"


def test_protect_rejects_already_encrypted(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)
    first = protect(_request("protect", inputs=[doc], options={"password": "a"}, output_dir=output_dir))

    result = protect(_request("protect", inputs=[first.outputs[0]], options={"password": "b"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "ALREADY_ENCRYPTED"


def test_unlock_rejects_wrong_password(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)
    protected = protect(_request("protect", inputs=[doc], options={"password": "correct"}, output_dir=output_dir))

    result = unlock(_request("unlock", inputs=[protected.outputs[0]], options={"password": "wrong"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "WRONG_PASSWORD"


def test_unlock_rejects_non_encrypted_pdf(make_pdf, output_dir):
    doc = make_pdf("doc.pdf", pages=1)

    result = unlock(_request("unlock", inputs=[doc], options={"password": "anything"}, output_dir=output_dir))

    assert result.status == "error"
    assert result.error.code == "NOT_ENCRYPTED"
