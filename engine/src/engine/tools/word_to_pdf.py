"""Word to PDF: convert a DOCX/DOC file to PDF via headless LibreOffice."""

from __future__ import annotations

from engine.tools.office_convert import make_office_to_pdf_tool

word_to_pdf = make_office_to_pdf_tool({".doc", ".docx"})
