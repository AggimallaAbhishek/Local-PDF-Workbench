# Local PDF Workbench

A private, offline-first desktop PDF toolkit — merge, split, convert, secure, and
clean up PDFs entirely on your own machine. No upload, no cloud API, no
telemetry, ever, for core functionality. The app must be fully usable with the
network interface disabled.

Full architecture, job contract, and roadmap live in [PLAN.md](PLAN.md). This
file tracks what's actually built.

## Stack

| Layer | Choice |
|---|---|
| Desktop shell | Tauri 2 (Rust) |
| Frontend | React + TypeScript + Tailwind CSS |
| Processing engine | Python (subprocess, JSON over stdin/stdout) |
| PDF libraries | pypdf, PyMuPDF, pikepdf |
| Images | Pillow |
| Overlays | reportlab |
| OCR | Tesseract (via pytesseract) — system install required |
| Office conversion | LibreOffice headless (`soffice`) — system install required |

The UI never touches document bytes directly — it calls Tauri commands with
paths and settings, which spawn the Python engine as a one-shot subprocess per
job (see `apps/desktop/src-tauri/src/job.rs` and
`engine/src/engine/app/main.py`).

## Status

**Sprints 1–4 (MVP), all of Phase 2, and most of Phase 3 are done.** 26 of
PLAN.md's 29 tools work end to end, backed by 94 Python tests and 4 Rust
tests, all passing.

### Sprint 1 — Desktop shell
Tauri + React dashboard, category filters, search, tool cards, privacy
indicator. `apps/desktop/src/pages/Dashboard.tsx`.

### Sprint 2 — Job pipeline
`run_job` Tauri command spawns the Python engine, native file/output-dir
pickers, structured `JobResult` success/error contract shared across
TypeScript, Rust, and Python.

### Sprint 3 — Page management (MVP)
merge · split · rotate · organize · preview (page thumbnails), each with a
full tool workspace (input picker, page selection/reorder, output picker,
result panel).

### Sprint 4 — MVP processing set complete
compress · watermark · page numbers · PDF→JPG · JPG→PDF.

### Phase 2 — Security & advanced document tools (10 of 10)
crop · protect (encrypt) · unlock · repair · redact · sign · compare ·
convert to PDF/A · scan import · edit & annotate.

Redact uses PyMuPDF's redaction API, verified to actually strip the
underlying text (not just paint over it) — checked against both extracted
text and the saved file's raw bytes. PDF/A conversion is explicitly
best-effort: it embeds identification metadata and a color output intent but
doesn't validate full conformance, and says so on every run. Edit & Annotate
is the one interactive tool in the app — an SVG canvas over the page preview
for placing text, rectangles, and lines, converted to PDF point coordinates
and baked permanently into the page via the same overlay pattern as
watermark/page numbers (not interactive PDF annotation objects, which render
inconsistently across viewers).

### Phase 3 — Office conversion, OCR, Markdown (6 of 9)
word-to-pdf · excel-to-pdf · ppt-to-pdf · html-to-pdf · markdown-to-pdf ·
OCR · fill forms.

OCR renders each page, runs Tesseract, and overlays an invisible text layer
back onto the *original* page content (reportlab text render mode 3) —
verified end to end: a page with zero extractable text gets exactly the
recognized words back via an independent parser, with the original image
still present. Office-to-PDF conversion shells out to headless LibreOffice.

**Deliberately not built: pdf-to-word, pdf-to-excel, pdf-to-ppt.** This
isn't a scoping choice — LibreOffice headless cannot do it. Opening a PDF
routes it into Draw, and Draw has no export filter to Writer/Calc/Impress
formats at all (confirmed directly: docx, odt, xlsx, and pptx targets all
fail with "no export filter"). Shipping these would mean either failing
every time or producing something misleadingly poor, so they're left
unavailable rather than faked.

**Not yet built:** the Advanced tier (local AI, batch processing, local
search).

### Hardening pass
A code review (Standards + Spec axes against PLAN.md) surfaced four real
issues, since fixed and covered by regression tests:
- output moves are now atomic even when the output folder is on a different
  filesystem than the temp workspace (e.g. an external drive)
- every generated file is re-opened with an independent parser before being
  reported as a success, not just checked for "exists and non-empty"
- an unexpected engine error no longer surfaces raw exception text to the UI
  (only the exception type; full detail goes to stderr)
- "Open" / "Show in folder" are now mediated by two narrowly-scoped Rust
  commands instead of an unscoped plugin permission

Known gap, not yet addressed: there's no persistent Job Manager (progress
tracking, cancellation, SQLite job history) — `run_job` is currently a
one-shot blocking call per PLAN.md §3's simpler description, not the fuller
Job Manager described in §3's architecture diagram.

## Repository layout

```
apps/desktop/          Tauri + React frontend
  src/features/         one folder per tool (workspace UI)
  src/services/         Tauri command wrappers (engine, files, preview)
  src-tauri/src/         job.rs (job runner), output.rs (mediated file open)
engine/                 Python processing engine
  src/engine/tools/      one module per tool + shared plumbing (common.py, office_convert.py)
  tests/                 pytest suite (94 tests)
PLAN.md                 full architecture, job contract, roadmap, security requirements
```

## Running it

```bash
# System dependencies for OCR and Office conversion (macOS/Homebrew)
brew install tesseract
brew install --cask libreoffice

# Engine
cd engine && uv sync && uv run pytest

# Desktop app
cd apps/desktop
npm install
npm run tauri dev
```
