"""Maps a job's `tool` name to its implementation.

Empty until Sprint 3 starts implementing individual tools (merge, split,
rotate, ...). Each entry will be a callable: JobRequest -> JobResult.
"""

from __future__ import annotations

from collections.abc import Callable

from engine.jobs.contract import JobRequest, JobResult

ToolHandler = Callable[[JobRequest], JobResult]

REGISTRY: dict[str, ToolHandler] = {}


def get_handler(tool: str) -> ToolHandler | None:
    return REGISTRY.get(tool)
