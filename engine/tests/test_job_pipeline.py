"""Sprint 2 exit criterion: the request -> handler -> structured result
pipeline works, for both the unimplemented-tool path and a registered one.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys

import engine.app.main as main_module
from engine.app.main import handle
from engine.jobs.contract import JobRequest, JobResult
from engine.tools import registry


def _sample_request(**overrides) -> dict:
    base = {
        "jobId": "job-1",
        "tool": "does-not-exist",
        "inputs": [],
        "options": {},
        "outputDir": "/tmp",
    }
    base.update(overrides)
    return base


def test_unknown_tool_returns_structured_error():
    result = handle(_sample_request())
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "TOOL_NOT_IMPLEMENTED"
    assert result.job_id == "job-1"


def test_registered_tool_runs_and_returns_success():
    def fake_handler(request: JobRequest) -> JobResult:
        return JobResult.ok(request.job_id, outputs=[f"{request.output_dir}/out.pdf"])

    registry.REGISTRY["fake-tool"] = fake_handler
    try:
        result = handle(_sample_request(tool="fake-tool", outputDir="/tmp"))
    finally:
        del registry.REGISTRY["fake-tool"]

    assert result.status == "success"
    assert result.outputs == ["/tmp/out.pdf"]


def test_engine_subprocess_round_trips_json():
    """Exercises the exact boundary the Tauri `run_job` command crosses:
    one JSON request on stdin, one JSON JobResult on stdout, non-zero exit
    never happens even for a bad tool name.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "engine.app.main"],
        input=json.dumps(_sample_request()),
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "TOOL_NOT_IMPLEMENTED"


def test_unexpected_error_does_not_leak_exception_text_to_the_caller(monkeypatch, capsys):
    """PLAN.md §3/§8: a JobResult error must never include document
    content. The top-level catch-all in main() is a much wider net than
    any individual tool's curated ToolErrors - an unexpected exception
    there (a real engine bug) must not ship its raw exception text to the
    caller, since that text could contain fragments of whatever it was
    processing. Full detail should still reach stderr for local debugging.
    """
    sensitive_marker = "super-secret-document-content-12345"

    def boom(_raw_request):
        raise ValueError(sensitive_marker)

    monkeypatch.setattr(main_module, "handle", boom)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(_sample_request())))

    main_module.main()

    captured = capsys.readouterr()
    assert sensitive_marker not in captured.out
    payload = json.loads(captured.out)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "ENGINE_ERROR"
    assert sensitive_marker in captured.err, "full detail should still be available on stderr for debugging"
