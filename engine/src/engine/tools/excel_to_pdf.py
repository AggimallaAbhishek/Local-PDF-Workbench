"""Excel to PDF: convert an XLSX/XLS file to PDF via headless LibreOffice."""

from __future__ import annotations

from engine.tools.office_convert import make_office_to_pdf_tool

excel_to_pdf = make_office_to_pdf_tool({".xls", ".xlsx"})
