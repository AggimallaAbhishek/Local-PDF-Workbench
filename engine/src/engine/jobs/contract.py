"""Job contract shared with the Tauri/React frontend.

Keep in sync with apps/desktop/src/types/job.ts — this is the Python side
of the single JSON shape that crosses the Tauri <-> Python boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

JobStatus = Literal["success", "error", "cancelled"]


@dataclass
class JobRequest:
    job_id: str
    tool: str
    inputs: list[str]
    options: dict[str, Any]
    output_dir: str
    overwrite_original: bool = False

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "JobRequest":
        return JobRequest(
            job_id=data["jobId"],
            tool=data["tool"],
            inputs=list(data["inputs"]),
            options=dict(data.get("options", {})),
            output_dir=data["outputDir"],
            overwrite_original=bool(data.get("overwriteOriginal", False)),
        )


@dataclass
class JobError:
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass
class JobResult:
    job_id: str
    status: JobStatus
    outputs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: JobError | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "jobId": self.job_id,
            "status": self.status,
            "outputs": self.outputs,
            "metadata": self.metadata,
            "warnings": self.warnings,
        }
        if self.error is not None:
            result["error"] = self.error.to_dict()
        return result

    @staticmethod
    def ok(job_id: str, outputs: list[str], metadata: dict[str, Any] | None = None,
           warnings: list[str] | None = None) -> "JobResult":
        return JobResult(
            job_id=job_id,
            status="success",
            outputs=outputs,
            metadata=metadata or {},
            warnings=warnings or [],
        )

    @staticmethod
    def failed(job_id: str, code: str, message: str) -> "JobResult":
        return JobResult(job_id=job_id, status="error", error=JobError(code, message))
