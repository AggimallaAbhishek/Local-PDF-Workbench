# Local PDF Workbench

A private, offline-first desktop PDF toolkit — merge, split, convert, secure, and
clean up PDFs entirely on your own machine. No upload, no cloud API, no
telemetry, ever, for core functionality. The app must be fully usable with the
network interface disabled.

Full architecture, job contract, and roadmap live in [PLAN.md](PLAN.md). This
file tracks what's actually built. For using the app itself — supported
formats, known limitations, troubleshooting — see
[docs/user-guide.md](docs/user-guide.md).

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
| Local AI | llama.cpp (via llama-cpp-python) + Qwen2.5-1.5B-Instruct GGUF — model download required |

The UI never touches document bytes directly — it calls Tauri commands with
paths and settings, which spawn the Python engine as a one-shot subprocess per
job (see `apps/desktop/src-tauri/src/job.rs` and
`engine/src/engine/app/main.py`).

## Status

**Sprints 1–4 (MVP), all of Phase 2, most of Phase 3, all of the Advanced
tier, and Phase 5 hardening are done.** 31 of PLAN.md's 34 tools work end
to end (28 real engine tools + Batch/Workflow Builder, which reuse the
others, + Search), backed by 109 Python tests and 12 Rust tests, all
passing.

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

### Advanced tier — Workflow Builder, Batch Processing, Search, Summarize, Translate (5 of 5)
None of these needed new engine tools — they're frontend orchestration over
the existing job runner:
- **Batch Processing** runs one tool across every matching file in a folder,
  sequentially, with live per-file progress.
- **Workflow Builder** chains steps where each one's output feeds the next
  one's input, with intermediate files landing in the app's own cache dir
  (only the final step writes to the user's chosen folder).
- **Search** does an on-demand full-text scan across a folder's PDFs (no
  persistent index — that's a deliberate scope cut) and renders an HTML
  report plus inline results.

Both Batch and Workflow Builder share one declarative tool catalog
(`features/shared/pipelineTools.ts`) covering every tool whose options are
flat key/value pairs — a tool like Crop, whose options nest under
`margins`, doesn't fit that shape and isn't included there (its dedicated
workspace still works normally).

**Summarize, Translate (5 of 5 — Advanced tier complete):** run against a
local Qwen2.5-1.5B-Instruct model (Q4_K_M GGUF, ~1.1GB) via
`llama-cpp-python`/llama.cpp — verified with real inference, not mocked
(both produce a coherent output; translation was checked for actual target-
language content). The model isn't bundled in the repo (a ~1GB binary,
gitignored under `models/`) — download it once, see "Running it" below.
Since jobs are one-shot subprocesses with no state between them, the model
loads fresh each call (~12s) before generating (~1s) — a known trade-off of
that architecture, not something fixed here. Long documents are truncated
to fit the model's 4096-token context window, with an explicit warning
when that happens rather than silently summarizing only part of a
document.

### Code-review hardening pass
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

### Job Manager (PLAN.md §3)
`run_job` is still a one-shot subprocess per job (an intentional
architecture choice from Sprint 2 — a crashed job can never leak state into
the next one), but the pieces §3's architecture diagram calls for around it
are now real:
- **Persisted history** — every job is recorded to a SQLite database in the
  app's own data directory (`jobs.db`, one row per job) when it starts and
  updated with its final status when it finishes. A "History" page (from
  the dashboard's top nav) lists past and in-flight jobs with their
  outputs, reachable via the same "Open"/"Show in folder" actions as a
  regular job result.
- **Cancellation** — a running job's OS process can be looked up by job ID
  and killed. Verified with a real test, not just logic review: spawns a
  genuinely long-running process, registers it, cancels it, and confirms
  the process actually died (not just that the code *would* have sent a
  signal) — cross-platform via `kill -9` (Unix) / `taskkill` (Windows).
  `run_job`'s own promise resolves with `status: "cancelled"` once this
  happens, since the same await that's already waiting on the subprocess
  naturally completes once it's killed — no separate signaling path needed
  between the two Tauri commands.
- This required moving `run_job` from a blocking `std::process::Command`
  call to `tokio::process::Command` + `async fn`, so a `cancel_job`
  invocation can run concurrently with an in-flight `run_job` rather than
  the whole IPC layer being blocked until the job finishes.

Not implemented: fine-grained progress percentages (e.g. "page 3 of 10").
That needs the engine to emit incremental events over the subprocess
boundary rather than one JSON blob at the end - a real protocol change
touching every tool, not just the Rust side, and a bigger scope than this
pass.

### Phase 5 — Hardening (in progress)

**Security review** (dedicated pass, separate from the code review above):
a threat-model-aware review across command injection, path traversal,
Tauri capability scope, unsafe deserialization, and data exposure found one
real defect — `output_filename()` didn't sanitize the `outputFilename` job
option, so an absolute path or `../` segments could steer a tool's write
(and later delete) outside the intended output directory. Fixed: it's now
reduced to a basename before use, with regression tests covering absolute
paths, traversal segments, and an end-to-end check that a malicious value
can't escape `outputDir`. Several other candidates (pypdf's default RC4-128
PDF encryption, LibreOffice macro execution in headless conversion, local
file references in HTML→PDF) were investigated and rejected after
verification — none were concretely exploitable in this app's actual
single-user local threat model (see the session record for the full
reasoning per candidate).

**Network/offline verification**: confirmed zero network capability at
every layer — no HTTP/updater plugin in the Rust `Cargo.toml`, no
network-capable npm dependencies or `fetch`/`XMLHttpRequest`/`WebSocket`
calls anywhere in the frontend, no remote font/CDN references, and no
network imports or calls anywhere in the Python engine or its dependencies
(pypdf/pikepdf/pymupdf/Pillow/reportlab/pytesseract/markdown/llama-cpp-python
are all local-only libraries). Verified at runtime, not just by reading
code: the entire engine test suite (109 tests, including real local-AI
inference) passes with `socket.socket.connect` and `socket.create_connection`
both patched to raise on any call — proving the Python engine itself never
attempts a connection, even when running the LLM — and a live `lsof`
socket check during a real LibreOffice conversion and a real Tesseract OCR
run found no open network sockets from either external binary.

**User-facing docs** now live at [docs/user-guide.md](docs/user-guide.md):
supported formats, known limitations per tool, and a troubleshooting table
keyed to every error code the engine actually returns.

**Packaging**: `npm run tauri build` produces a real `.app` and `.dmg`
(`apps/desktop/src-tauri/target/release/bundle/`), ad-hoc signed since
there's no Apple Developer certificate configured. Verified beyond "it
compiled": launched the built `.app` directly, confirmed the process stayed
running (not an immediate post-launch crash, which is how a broken Tauri
bundle typically fails), checked for crash reports (none), and quit it
cleanly. Not yet done: an actual install-from-`.dmg` walkthrough, and
Windows/Linux bundles (this was only built and verified on macOS/arm64).

Phase 5 is now functionally complete for a single-platform (macOS) release.

## Repository layout

```
apps/desktop/          Tauri + React frontend
  src/features/         one folder per tool (workspace UI); shared/pipelineTools.ts (Batch/Workflow catalog)
  src/services/         Tauri command wrappers (engine, files, preview)
  src-tauri/src/         job.rs (job runner + cancellation), jobs_db.rs (SQLite history),
                         output.rs (mediated file open), directory.rs (folder listing)
engine/                 Python processing engine
  src/engine/tools/      one module per tool + shared plumbing (common.py, office_convert.py, llm.py)
  tests/                 pytest suite (109 tests)
models/                 local AI model file (gitignored — download separately, see below)
PLAN.md                 full architecture, job contract, roadmap, security requirements
```

## Running it

```bash
# System dependencies for OCR and Office conversion (macOS/Homebrew)
brew install tesseract
brew install --cask libreoffice

# Local AI model for Summarize/Translate (~1.1GB) — optional, only needed for those two tools
curl -L -o models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"

# Engine
cd engine && uv sync && uv run pytest

# Desktop app
cd apps/desktop
npm install
npm run tauri dev
```
