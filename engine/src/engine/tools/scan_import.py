"""Scan import: turn one or more scanned photos into a clean PDF.

Builds on the same image-to-PDF path as jpg_to_pdf, with an optional
cleanup pass (grayscale + autocontrast) aimed at scanned document photos -
faded or unevenly lit paper scans usually get noticeably more readable
and compress better once flattened to high-contrast grayscale.

options:
  enhance: bool (default true)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_image, run_tool


def _load_and_clean(path: Path, enhance: bool) -> Image.Image:
    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_IMAGE", f"Could not read {path.name}: {exc}") from exc

    if enhance:
        img = ImageOps.autocontrast(ImageOps.grayscale(img))
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    return img


def _scan_import(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if not request.inputs:
        raise ToolError("INVALID_INPUT", "Scan import requires at least one input image.")

    enhance = bool(request.options.get("enhance", True))

    images = [_load_and_clean(require_input_image(raw_path), enhance) for raw_path in request.inputs]

    filename = output_filename(request.options, "outputFilename", "scanned.pdf")
    out_path = workspace / filename
    images[0].save(out_path, save_all=True, append_images=images[1:])

    metadata = {"pageCount": len(images), "enhanced": enhance}
    return [out_path], metadata, []


def scan_import(request: JobRequest) -> JobResult:
    return run_tool(request, _scan_import)
