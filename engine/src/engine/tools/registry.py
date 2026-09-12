"""Maps a job's `tool` name to its implementation."""

from __future__ import annotations

from collections.abc import Callable

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.merge import merge
from engine.tools.organize import organize
from engine.tools.preview import preview
from engine.tools.rotate import rotate
from engine.tools.split import split

ToolHandler = Callable[[JobRequest], JobResult]

REGISTRY: dict[str, ToolHandler] = {
    "merge": merge,
    "split": split,
    "rotate": rotate,
    "organize": organize,
    "preview": preview,
}


def get_handler(tool: str) -> ToolHandler | None:
    return REGISTRY.get(tool)
