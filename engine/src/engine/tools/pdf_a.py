"""Convert to PDF/A: best-effort archival preparation.

IMPORTANT LIMITATION: this embeds the two structural pieces we can add
without re-rendering the document - an sRGB OutputIntent and PDF/A
identification XMP metadata (pdfaid:part / pdfaid:conformance) - and
normalizes the file via pikepdf/qpdf. It does NOT verify or guarantee full
PDF/A conformance (that also requires every font to already be embedded, no
encryption, no prohibited content types, etc.), and this tool cannot fix a
source PDF that violates those. Treat the output as "PDF/A-flavored", not
as a validated PDF/A file - real conformance needs a validator such as
veraPDF, which isn't bundled here. This is surfaced to the user as a
warning on every run, per PLAN.md's "document limits, warn in UI" policy.

options:
  conformance: "1B" | "2B" | "3B" (default "2B")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pikepdf
from PIL import ImageCms

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, output_filename, require_input_pdf, run_tool

VALID_CONFORMANCE = {"1B", "2B", "3B"}


def _srgb_icc_bytes() -> bytes:
    profile = ImageCms.createProfile("sRGB")
    return ImageCms.ImageCmsProfile(profile).tobytes()


def _pdf_a(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if len(request.inputs) != 1:
        raise ToolError("INVALID_INPUT", "Convert to PDF/A requires exactly one input PDF.")

    conformance = request.options.get("conformance", "2B")
    if conformance not in VALID_CONFORMANCE:
        raise ToolError("INVALID_OPTIONS", f"'conformance' must be one of {sorted(VALID_CONFORMANCE)}.")
    part = conformance[0]
    level = conformance[1]

    pdf_path = require_input_pdf(request.inputs[0])
    try:
        pdf = pikepdf.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError("UNREADABLE_PDF", f"Could not read {pdf_path.name}: {exc}") from exc

    try:
        icc_stream = pikepdf.Stream(pdf, _srgb_icc_bytes())
        icc_stream.N = 3
        output_intent = pdf.make_indirect(
            pikepdf.Dictionary(
                Type=pikepdf.Name("/OutputIntent"),
                S=pikepdf.Name("/GTS_PDFA1"),
                OutputConditionIdentifier="sRGB IEC61966-2.1",
                Info="sRGB IEC61966-2.1",
                DestOutputProfile=icc_stream,
            )
        )
        pdf.Root.OutputIntents = pikepdf.Array([output_intent])

        with pdf.open_metadata() as meta:
            meta["pdfaid:part"] = part
            meta["pdfaid:conformance"] = level

        page_count = len(pdf.pages)
        filename = output_filename(request.options, "outputFilename", f"{pdf_path.stem}_pdfa.pdf")
        out_path = workspace / filename
        pdf.save(str(out_path))
    finally:
        pdf.close()

    warnings = [
        "This is a best-effort PDF/A conversion (embeds an sRGB output intent and PDF/A "
        "identification metadata). It is not validated against the PDF/A specification - "
        "use a dedicated validator before relying on it for legal or archival compliance."
    ]
    metadata = {"pageCount": page_count, "conformance": f"PDF/A-{conformance}"}
    return [out_path], metadata, warnings


def pdf_a(request: JobRequest) -> JobResult:
    return run_tool(request, _pdf_a)
