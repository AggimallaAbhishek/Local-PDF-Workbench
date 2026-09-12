"""Engine entrypoint.

Invoked by the Tauri job manager as a subprocess: one JSON JobRequest is
passed on stdin, one JSON JobResult is written to stdout. Kept as a single
request/response call (not a long-lived server) so a crashed job can never
leak state into the next one.
"""

from __future__ import annotations

import json
import sys

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.registry import get_handler


def handle(raw_request: dict) -> JobResult:
    request = JobRequest.from_dict(raw_request)
    handler = get_handler(request.tool)
    if handler is None:
        return JobResult.failed(
            request.job_id,
            code="TOOL_NOT_IMPLEMENTED",
            message=f"No engine implementation for tool '{request.tool}' yet.",
        )
    return handler(request)


def main() -> None:
    raw_request: dict = {}
    try:
        raw_request = json.loads(sys.stdin.read())
        result = handle(raw_request)
    except Exception as exc:  # noqa: BLE001 - top-level boundary, must not crash silently
        # Unlike a tool's curated ToolError, this catches literally anything,
        # so exc's own text is not trusted to be free of document content -
        # only the exception type crosses this boundary. Full detail still
        # goes to stderr for local debugging.
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        result = JobResult.failed(
            raw_request.get("jobId", "unknown"),
            code="ENGINE_ERROR",
            message=f"An unexpected internal error occurred ({type(exc).__name__}).",
        )
    json.dump(result.to_dict(), sys.stdout)


if __name__ == "__main__":
    main()
