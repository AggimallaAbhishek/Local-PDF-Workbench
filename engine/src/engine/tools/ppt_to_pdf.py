"""PowerPoint to PDF: convert a PPTX/PPT file to PDF via headless LibreOffice."""

from __future__ import annotations

from engine.tools.office_convert import make_office_to_pdf_tool

ppt_to_pdf = make_office_to_pdf_tool({".ppt", ".pptx"})
