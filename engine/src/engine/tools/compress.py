"""Compress: reduce PDF file size via image downsampling + stream compression.

Recompresses each embedded raster image as JPEG at the chosen quality and
re-saves the PDF with generated object streams (pikepdf). Images are only
replaced when doing so actually shrinks them — for photo-like content this
wins big; for already-compressed or synthetic content it can lose, so we
measure rather than assume. Indexed, non-8-bit, and alpha-masked images are
left untouched: recompressing them as JPEG would need palette/alpha handling
this tool doesn't attempt, and a wrong guess would degrade the image.

options:
  quality: "low" | "medium" | "high" (default "medium")
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pikepdf
from PIL import Image

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool

QUALITY_PRESETS = {"low": 35, "medium": 60, "high": 80}


def _recompress_images(pdf: pikepdf.Pdf, jpeg_quality: int) -> tuple[int, int]:
    recompressed = 0
    skipped = 0

    for page in pdf.pages:
        for raw_image in page.get_images().values():
            try:
                pdf_image = pikepdf.PdfImage(raw_image)
                if pdf_image.indexed or pdf_image.bits_per_component != 8 or "/SMask" in raw_image:
                    skipped += 1
                    continue

                pil_image = pdf_image.as_pil_image()
                if pil_image.mode not in ("RGB", "L"):
                    pil_image = pil_image.convert("RGB")

                buf = io.BytesIO()
                pil_image.save(buf, format="JPEG", quality=jpeg_quality)
                new_bytes = buf.getvalue()

                if len(new_bytes) >= len(raw_image.read_raw_bytes()):
                    skipped += 1
                    continue

                raw_image.write(new_bytes, filter=pikepdf.Name("/DCTDecode"))
                recompressed += 1
            except Exception:  # noqa: BLE001 - one bad image must not fail the whole job
                skipped += 1

    return recompressed, skipped


def _compress(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Compress requires exactly one input PDF.")

    quality_key = request.options.get("quality", "medium")
    if quality_key not in QUALITY_PRESETS:
        raise ToolError("INVALID_OPTIONS", f"'quality' must be one of {sorted(QUALITY_PRESETS)}.")

    pdf_path = require_input_pdf(request.inputs[0])
    original_size = pdf_path.stat().st_size

    try:
        pdf = pikepdf.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    try:
        recompressed, skipped = _recompress_images(pdf, QUALITY_PRESETS[quality_key])

        filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_compressed.pdf")
        out_path = workspace / filename
        pdf.save(
            str(out_path),
            compress_streams=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
        )
    finally:
        pdf.close()

    compressed_size = out_path.stat().st_size
    warnings = []
    if compressed_size >= original_size:
        warnings.append("Compressed file was not smaller than the original; it may already be optimized.")

    metadata = {
        "originalSizeBytes": original_size,
        "compressedSizeBytes": compressed_size,
        "imagesRecompressed": recompressed,
        "imagesSkipped": skipped,
    }
    return [out_path], metadata, warnings


def compress(request: JobRequest) -> JobResult:
    return run_tool(request, _compress)
