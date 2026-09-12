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
        result = JobResult.failed(raw_request.get("jobId", "unknown"), code="ENGINE_ERROR", message=str(exc))
    json.dump(result.to_dict(), sys.stdout)


if __name__ == "__main__":
    main()
