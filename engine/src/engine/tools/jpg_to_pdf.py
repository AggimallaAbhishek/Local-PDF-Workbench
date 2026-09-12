"""JPG to PDF: combine one or more images into a single PDF, one per page,
in the given order.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, run_tool

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}


def _require_input_image(path: str) -> Path:
    p = Path(path)
    if not p.is_file():
        raise ToolError("INPUT_NOT_FOUND", f"Input file not found: {p.name}")
    if p.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ToolError("INPUT_NOT_IMAGE", f"Unsupported image type: {p.name}")
    return p


def _jpg_to_pdf(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if not request.inputs:
        raise ToolError("INVALID_INPUT", "JPG to PDF requires at least one input image.")

    images = []
    for raw_path in request.inputs:
        image_path = _require_input_image(raw_path)
        try:
            img = Image.open(image_path)
            img.load()
        except Exception as exc:  # noqa: BLE001
            raise ToolError("UNREADABLE_IMAGE", f"Could not read {image_path.name}: {exc}") from exc

        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        images.append(img)

    filename = output_filename(request.options, "outputFilename", "images.pdf")
    out_path = workspace / filename
    images[0].save(out_path, save_all=True, append_images=images[1:])

    metadata = {"pageCount": len(images)}
    return [out_path], metadata, []


def jpg_to_pdf(request: JobRequest) -> JobResult:
    return run_tool(request, _jpg_to_pdf)
