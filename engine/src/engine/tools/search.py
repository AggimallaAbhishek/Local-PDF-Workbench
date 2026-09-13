"""Search: full-text search across a set of local PDFs.

Scans on demand (extracts text per page via pypdf and does a substring
match) - no persistent index. That's a deliberate scope choice: an index
implies a database file, staleness/refresh handling, and a lot more
surface area than PLAN.md's "local full-text search" asks for. Local
semantic (embeddings) search is a separate, explicitly-future feature.

options:
  query: str (required)
  caseSensitive: bool (default false)

Unreadable inputs are skipped (with a warning), not fatal - a search
across a folder shouldn't fail entirely because one file is corrupt.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from engine.jobs.contract import JobRequest, JobResult
from engine.tools.common import ToolError, run_tool

CONTEXT_CHARS = 40
MAX_MATCHES_IN_METADATA = 200


def _find_matches(text: str, needle: str, case_sensitive: bool) -> list[str]:
    haystack = text if case_sensitive else text.lower()
    snippets = []
    idx = haystack.find(needle)
    while idx != -1:
        start = max(0, idx - CONTEXT_CHARS)
        end = min(len(text), idx + len(needle) + CONTEXT_CHARS)
        snippets.append(text[start:end].replace("\n", " ").strip())
        idx = haystack.find(needle, idx + len(needle))
    return snippets


def _build_report(query: str, matches: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"<tr><td>{html.escape(m['file'])}</td><td>{m['page']}</td>"
        f"<td>{html.escape(m['snippet'])}</td></tr>"
        for m in matches
    )
    body = (
        f"<p>{len(matches)} match(es) for <strong>{html.escape(query)}</strong></p>"
        f"<table border='1' cellpadding='6' cellspacing='0'>"
        f"<thead><tr><th>File</th><th>Page</th><th>Context</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        if matches
        else f"<p>No matches for <strong>{html.escape(query)}</strong>.</p>"
    )
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Search Results</title></head><body>{body}</body></html>"


def _search(request: JobRequest, workspace: Path) -> tuple[list[Path], dict[str, Any], list[str]]:
    if not request.inputs:
        raise ToolError("INVALID_INPUT", "Search requires at least one input PDF.")

    query = request.options.get("query")
    if not query or not str(query).strip():
        raise ToolError("INVALID_OPTIONS", "'query' is required.")
    case_sensitive = bool(request.options.get("caseSensitive", False))
    needle = str(query) if case_sensitive else str(query).lower()

    matches: list[dict[str, Any]] = []
    skipped: list[str] = []

    for raw_path in request.inputs:
        path = Path(raw_path)
        if not path.is_file() or path.suffix.lower() != ".pdf":
            skipped.append(path.name)
            continue
        try:
            reader = PdfReader(str(path))
        except Exception:  # noqa: BLE001 - one bad file must not abort the whole search
            skipped.append(path.name)
            continue

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            for snippet in _find_matches(text, needle, case_sensitive):
                matches.append({"file": path.name, "path": str(path), "page": page_number, "snippet": snippet})

    out_path = workspace / "search_results.html"
    out_path.write_text(_build_report(str(query), matches), encoding="utf-8")

    warnings = []
    if skipped:
        warnings.append(f"{len(skipped)} file(s) could not be read and were skipped: {skipped}")

    metadata = {
        "query": query,
        "matchCount": len(matches),
        "matches": matches[:MAX_MATCHES_IN_METADATA],
        "filesScanned": len(request.inputs) - len(skipped),
        "filesSkipped": skipped,
    }
    return [out_path], metadata, warnings


def search(request: JobRequest) -> JobResult:
    return run_tool(request, _search)
