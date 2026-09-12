# Local PDF Workbench — Development Plan

Source: `local_pdf_workbench_complete_project_plan.pdf`. This document translates that
blueprint into an actionable build plan: concrete repo layout, a real job contract,
and phase-by-phase task checklists we will work through in order.

## 1. What we're building

A **private, offline-first desktop PDF application** — a personal toolkit (merge,
split, convert, OCR, edit, optionally local-AI) modeled on an iLovePDF-style
dashboard, but where every operation runs on the user's machine. No upload, no
cloud API, no telemetry, ever, for core functionality.

**Non-negotiable design rule:** the app must be fully usable with the network
interface disabled. If a feature can't work offline, it doesn't ship in that form.

### Explicitly out of scope (v1)
- Cloud storage, accounts, online collaboration, remote processing.
- Payments / subscriptions.
- Silent cloud fallback when a local op fails.
- Guaranteed pixel-perfect Office conversion for every document.
- Password bypass / unauthorized decryption.

## 2. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Desktop shell | **Tauri 2** | packaging, windowing, permission-scoped commands |
| Frontend | **React + TypeScript** | dashboard, tool workspaces, previews |
| Styling | **Tailwind CSS** | |
| Processing engine | **Python** | invoked as a sidecar/subprocess from Tauri |
| PDF libs | **pypdf**, **PyMuPDF (fitz)**, **pikepdf** | page ops, rendering, low-level object access |
| OCR | **Tesseract** (via `pytesseract`) | local text recognition |
| Office conversion | **LibreOffice** (headless, `soffice --convert-to`) | DOCX/XLSX/PPTX |
| Images | **Pillow** | JPG↔PDF, downsampling |
| Overlays | **reportlab** | watermark / page-number generation |
| Local persistence | **SQLite** | prefs, job history, presets |
| Optional local AI | **llama.cpp** or similar local runtime | summarization/translation, strictly opt-in |

All dependencies pinned; lockfiles committed; licenses documented in `docs/`.

## 3. Architecture

```
React/TS UI  →  Tauri commands (permission-scoped)  →  Job Manager
                                                          │
                                                          ▼
                                          Python engine (subprocess, JSON stdio)
                                                          │
                                                          ▼
                                     pypdf / PyMuPDF / pikepdf / Tesseract / LibreOffice / Pillow
                                                          │
                                                          ▼
                              filesystem (input dirs, temp dir, output dir) + SQLite (metadata)
```

- The UI never touches document bytes directly — it only calls Tauri commands with
  paths + settings and renders results/previews the engine produces.
- Tauri restricts filesystem/process capabilities to exactly what's needed
  (`src-tauri/capabilities/*.json`).
- The Job Manager assigns job IDs, validates inputs before invoking Python, tracks
  progress/cancellation, and persists job metadata to SQLite.

### Job contract (all tools implement this shape)

**Request (TS → Rust → Python, JSON):**
```ts
interface JobRequest {
  jobId: string;
  tool: string;                 // e.g. "merge", "split", "compress"
  inputs: string[];             // absolute local paths, pre-validated
  options: Record<string, unknown>; // tool-specific settings
  outputDir: string;
  overwriteOriginal?: boolean;  // default false
}
```

**Response (Python → Rust → TS, JSON):**
```ts
interface JobResult {
  jobId: string;
  status: "success" | "error" | "cancelled";
  outputs: string[];
  metadata?: Record<string, unknown>; // page counts, sizes, timing
  warnings: string[];
  error?: { code: string; message: string }; // never includes doc content
}
```

Processing sequence: **validate inputs → execute in temp dir → validate output →
atomically move to `outputDir` → report result → clean up temp dir.**
Original input files are never modified unless `overwriteOriginal` is explicitly set.

## 4. Repository structure

```
local-pdf-workbench/
├── apps/
│   └── desktop/
│       ├── src/                       # React/TS frontend
│       │   ├── components/
│       │   ├── pages/
│       │   ├── features/
│       │   │   ├── merge/
│       │   │   ├── split/
│       │   │   ├── compress/
│       │   │   ├── organize/
│       │   │   └── convert/
│       │   ├── services/              # Tauri command wrappers
│       │   └── types/
│       └── src-tauri/
│           ├── src/                   # Rust commands, job manager glue
│           └── capabilities/          # permission scoping
├── engine/                            # Python processing engine
│   ├── app/
│   ├── jobs/                          # job orchestration, JSON I/O
│   ├── tools/                         # merge.py, split.py, compress.py, ...
│   ├── converters/                    # office/image conversion
│   ├── security/                      # redaction, encryption
│   └── validation/
├── tests/
├── assets/
├── models/                            # local OCR/AI models (gitignored, user-managed)
├── docs/
├── scripts/
├── pyproject.toml
├── package.json
└── README.md
```

## 5. Feature roadmap

| Stage | Tools | Priority |
|---|---|---|
| **MVP** | merge, split, rotate, organize pages, compress, watermark, page numbers, PDF→JPG, JPG→PDF, preview | Must have |
| **Phase 2** | edit/annotate, redact, crop, repair, protect (encrypt), unlock (known password), sign, compare, PDF/A, scan import | High |
| **Phase 3** | PDF↔Word, PDF↔Excel, PDF↔PowerPoint, HTML→PDF, forms, OCR, Markdown | High |
| **Advanced** | local summarizer, offline translation, workflow builder, batch processing, local document search, presets | Optional |

Implementation notes:
- **Page ops** (merge/split/rotate/organize): `pypdf`; validate page counts + output readability.
- **Compression**: object stream optimization + image downsampling via `pikepdf`/Pillow; expose quality/size slider.
- **Watermark/page numbers**: overlay pages via `reportlab`, merged with `pypdf`.
- **Preview**: render thumbnails with PyMuPDF.
- **Redaction**: must strip content permanently (rebuild page content streams), never just draw a black box over text.
- **OCR**: render page → Tesseract → insert invisible searchable text layer.
- **Office conversion**: headless LibreOffice; report layout-fidelity limitations in the UI.
- **AI/translation**: bundled or user-installed local models only; never a silent cloud fallback.

## 6. UI plan

**Dashboard:** top nav (name, search, settings, privacy indicator, version) →
category filters (all, organize, optimize, convert, edit, security, intelligence,
workflows) → tool cards (icon, name, description, favorite, recent) → quick actions
(open file/folder, recent jobs, new workflow). Privacy indicator always visibly
states processing is local.

**Tool workspace:**
| Panel | Contents |
|---|---|
| Input | file picker, drag-drop, file list, validation, page count |
| Options | tool settings, presets, quality/page-range controls |
| Preview | thumbnails, rendered preview, before/after |
| Actions | start / cancel / reset / save preset / choose output dir |
| Result | output filename, size, warnings, validation status, open-folder |

## 7. Milestones (~10–14 weeks, solo dev pace — adjust as we go)

| Phase | Deliverables | Exit criteria |
|---|---|---|
| 0. Planning (this doc) | requirements, architecture, repo scaffold | scope agreed |
| 1. Desktop shell | Tauri app, dashboard, categories, search, settings, file picker | dashboard runs & navigates locally |
| 2. Core engine | merge, split, rotate, organize, compress, watermark, page numbers, image conversion | tools produce valid, tested outputs |
| 3. Advanced document tools | edit, redact, security, OCR, Office conversion, Markdown, PDF/A | supported formats work, limitations documented |
| 4. Local intelligence | optional AI, translation, workflows, batch, search | works fully offline |
| 5. Hardening | security review, network tests, packaging, docs | offline install + release checklist pass |

### First four sprints (where we actually start)
1. **Sprint 1** — init repo, configure Tauri/React/TS/Python, dashboard shell, define job contract → app launches, shows tool cards.
2. **Sprint 2** — file/output-dir selection, Python engine runner, structured job status/errors → one working end-to-end local job pipeline.
3. **Sprint 3** — merge, split, rotate, organize + preview/page selection → reliable page-management toolkit.
4. **Sprint 4** — compression, watermark, page numbers, JPG conversion, automated tests → MVP processing set complete.

## 8. Privacy & security requirements (testable, not aspirational)

| Control | Requirement |
|---|---|
| Network | zero remote calls/telemetry/analytics/fallback; test with network disabled |
| Tauri permissions | scoped to exactly the paths/commands needed |
| Local models | stored locally; location/size shown in UI |
| Temp files | app-controlled temp dir; wiped after success or cancel |
| Logging | never log document content, extracted text, passwords, tokens |
| Output safety | write to temp → validate → atomic move to final path |
| Dependencies | pinned versions, lockfiles, documented licenses, verified binaries |
| Access control | relies on OS account perms + disk encryption |
| Release gate | network-monitored offline test pass required before ship |

## 9. Testing strategy

- **Corpus:** text PDFs, scanned/OCR PDFs, image-heavy/large PDFs, tables/fonts/forms/annotations, password-protected (known password), malformed/damaged files, unusual page sizes/rotations.
- **Unit:** page ranges, settings validation, filename handling, error conditions.
- **Integration:** full Tauri→Python pipeline per tool.
- **Output validation:** re-open generated PDFs with an independent parser, compare page count/content.
- **Security:** run fully offline, monitor connections, inspect logs for leakage.
- **Performance:** timing/memory across small/medium/large files.
- **Recovery:** interrupt jobs, kill app, simulate low disk space — verify cleanup.
- **UX:** accessibility, keyboard nav, error clarity, progress feedback.

## 10. Key risks

| Risk | Mitigation |
|---|---|
| Complex layouts convert poorly | document limits, preserve original, warn in UI |
| Large PDFs blow memory | stream/page-by-page processing, cap concurrency |
| Low OCR accuracy | language settings, preview, allow reprocessing |
| A dependency phones home | audit + pin deps, offline tests, firewall rules in CI |
| Temp files survive crashes | job-scoped temp dirs, cleanup-on-startup |
| Encryption/permission confusion | require real passwords, never claim bypass |
| Local AI too heavy | make optional, show hardware requirements |
| Cross-platform drift | ship one OS first, then port |

## 11. MVP definition of done

- Launches with network disabled.
- Dashboard: search, categories, navigation all work.
- merge, split, rotate, organize, compress, watermark, page numbers, PDF→JPG, JPG→PDF all work.
- Native file/output-dir pickers; originals preserved by default.
- Every success path validates output before reporting success.
- Errors are readable and never leak document content.
- Temp files cleaned up on completion and cancellation.
- No MVP feature needs a network connection.
- Automated tests cover core ops + invalid input.
- Clean offline install builds and runs on the target OS.
- Docs cover supported formats, limitations, privacy behavior, troubleshooting.

## 12. Immediate next steps (starting point for development)

1. Pick first target OS (recommend: whichever the developer runs daily — start with one, port later).
2. Scaffold the repo per §4, lock dependency versions.
3. Write the privacy policy as an engineering spec (testable claims, not marketing copy).
4. Build Tauri + React dashboard shell with one reusable tool-card component.
5. Build the Python engine with a single `merge` operation returning the JSON job contract from §3.
6. Wire dashboard → engine through one controlled Tauri command end-to-end.
7. Add automated tests + a small non-sensitive PDF test corpus under `tests/fixtures/`.
8. Complete remaining MVP tools before touching editing/Office/AI features.
9. Run offline network-traffic monitoring + packaging validation before declaring MVP done.

**Starting point:** a trustworthy 8–10-tool MVP — preserves originals, validates
output, handles errors cleanly, works fully offline — matters more than dashboard
polish or tool count.

## 13. Future enhancements (post-MVP backlog)

Batch folder processing with naming templates · reusable presets ("compress for
email", "prepare archival PDF") · visual workflow builder (merge → compress →
watermark → export) · local full-text search · local semantic search (embeddings)
· document compare (visual + text-diff) · digital signatures with local certs ·
plugin architecture · encrypted local workspace · portable/external-drive mode.

---

Next action: scaffold the repo (§4) and start Sprint 1.
