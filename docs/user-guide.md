# Local PDF Workbench — User Guide

This is the guide for people *using* the app. If you're looking for
architecture, the job contract, or what's built vs. planned, see
[PLAN.md](../PLAN.md) and [README.md](../README.md) instead.

## Privacy

Everything runs on your own machine. Opening a file, choosing an output
folder, and running a tool never sends anything over the network — there is
no upload, no analytics, no telemetry, no update check, and no cloud
fallback if a local operation fails. This isn't just a policy: it's been
verified in code (no network-capable library is used anywhere in the app or
its processing engine) and at runtime (the entire engine test suite passes
with outbound network connections forcibly blocked at the OS-socket level,
and the external tools it calls — LibreOffice, Tesseract — were monitored
live and made no network connections during real conversions).

The one exception to "everything stays local" is that **you** choose where
output files go — the app writes exactly where you tell it to (your chosen
output folder), plus a small app-managed cache folder for ephemeral things
like page-preview thumbnails, which is cleaned up automatically over time
and never leaves your machine either.

Your original files are never modified. Every tool writes a new file;
nothing is overwritten unless you explicitly pick an output folder that
already contains a file with the same name, in which case you'll get a
numbered copy (`file (1).pdf`) rather than a silent overwrite.

## Supported formats

| Category | Tools | Input | Output |
|---|---|---|---|
| Organize | Merge, Split, Rotate, Organize Pages | PDF | PDF |
| Optimize | Compress, Repair | PDF | PDF |
| Edit | Watermark, Page Numbers, Crop, Edit & Annotate, Redact | PDF | PDF |
| Security | Protect, Unlock, Sign | PDF (+ PNG/JPG for a signature image) | PDF |
| Convert | PDF↔JPG, JPG/PNG→PDF, PDF/A, Import Scan | PDF, JPG, PNG | PDF, JPG |
| Convert (Office) | Word/Excel/PowerPoint/HTML/Markdown → PDF | DOC(X), XLS(X), PPT(X), HTML, MD | PDF |
| Intelligence | Compare, OCR, Search, Summarize, Translate | PDF | PDF, HTML report, plain text |
| Workflows | Batch Processing, Workflow Builder | varies by chosen tool | varies |

**Not supported:** PDF→Word, PDF→Excel, PDF→PowerPoint. This isn't a
missing feature we haven't gotten to — LibreOffice (the engine behind every
other Office conversion in this app) cannot do this conversion at all in
headless mode; it opens a PDF into its Draw module, which has no export
path to an editable Word/Excel/PowerPoint format. We'd rather leave these
unavailable than ship something that fails every time or produces garbage.

**Summarize and Translate need a one-time model download** (~1.1GB) —
they're built and work fully offline once the model file is in place, but
unlike every other tool, they need something beyond `npm install`/`uv
sync`. If you see a "model not found" error, see the download command in
the main [README](../README.md#running-it).

## Known limitations

- **Office conversions** (Word/Excel/PowerPoint/HTML/Markdown → PDF)
  preserve most text and layout but can shift formatting on complex
  documents — review the output before relying on it for anything
  layout-sensitive.
- **PDF/A conversion is best-effort.** It embeds the identification
  metadata and color profile a real PDF/A file needs, but doesn't verify
  full conformance (that also requires every font to already be embedded
  and no encryption, which this tool can't retroactively fix). Every run
  says so. If you need certified PDF/A compliance, check the output with a
  dedicated validator.
- **Redact matches exact, case-sensitive text only.** It permanently
  removes the matched text from the page (verified: it's gone from both
  extracted text and the file's raw bytes, not just painted over) — but
  text split across lines, or rendered with unusual fonts/kerning that
  breaks up how the text extracts, may not match. Always open the result
  and confirm before sharing a redacted document.
- **Sign** stamps an image onto the page — it does not add a cryptographic
  digital signature. Use it for a visual signature (e.g. a scanned or
  drawn signature image with a transparent background), not for
  legally-binding e-signing.
- **Compare** and **Search** work on extracted text only — they don't
  detect layout, image, or formatting differences, and Search has no
  persistent index; it re-scans the folder you point it at every time.
- **OCR** adds an invisible, searchable text layer over the original
  scanned image — it doesn't replace or clean up the image itself. Accuracy
  depends on scan quality and the DPI setting; try a higher DPI for small
  or faint text.
- **Summarize** and **Translate** run a small local model (1.5B parameters)
  — good for a quick gist or a rough translation, not a substitute for
  careful human review, especially for anything where translation accuracy
  matters. Long documents are truncated to what fits in the model's
  context window; you'll see a warning when that happens rather than a
  silently incomplete result. The first run after opening the app is
  slower (~10-15 seconds) while the model loads from disk.
- **Batch Processing** and **Workflow Builder** only support tools whose
  options are simple (a dropdown, a number, a bit of text) — a few tools
  with more structured options (like Crop's per-side margins) aren't in
  that list, but still work fine from their own dedicated tool page.
- There's no job history, progress bar for long-running jobs, or way to
  cancel a job in progress yet — a job runs to completion or failure as one
  step.

## Troubleshooting

Every error the app shows has a short code. Here's what the common ones mean:

| Code | Meaning |
|---|---|
| `INPUT_NOT_FOUND` / `INPUT_NOT_PDF` / `INPUT_NOT_IMAGE` / `INPUT_TYPE_INVALID` | The file you picked doesn't exist anymore, or isn't the type this tool expects. |
| `UNREADABLE_PDF` / `UNREADABLE_IMAGE` | The file exists but couldn't be parsed — it may be corrupted. Try **Repair PDF** first. |
| `UNREPAIRABLE` | Repair tried and couldn't recover the file. Some corruption is too severe to fix. |
| `PAGE_OUT_OF_RANGE` | A page number in your options doesn't exist in this document. |
| `WRONG_PASSWORD` | The password you gave **Unlock** doesn't match this file's password. |
| `NOT_ENCRYPTED` / `ALREADY_ENCRYPTED` | You tried to unlock a file that isn't password-protected, or protect one that already is. |
| `NO_FORM_FIELDS` | **Fill Forms** couldn't find any fillable fields in this PDF. |
| `OCR_ENGINE_NOT_FOUND` | Tesseract isn't installed. On macOS: `brew install tesseract`. |
| `OFFICE_ENGINE_NOT_FOUND` | LibreOffice isn't installed. On macOS: `brew install --cask libreoffice`. |
| `LOCAL_MODEL_NOT_FOUND` | **Summarize**/**Translate** need the local AI model downloaded first — see the README's "Running it" section. |
| `NO_TEXT_FOUND` | The PDF (or the pages you selected) has no extractable text to summarize/translate/search — likely a scanned document; try **OCR** first. |
| `CONVERSION_FAILED` / `CONVERSION_TIMED_OUT` | LibreOffice couldn't convert the file, or took too long. Very large or unusual documents can hit this. |
| `OUTPUT_DIR_INVALID` / `OUTPUT_DIR_NOT_CREATABLE` | The output folder you picked can't be used — check you have permission to write there. |
| `OUTPUT_VALIDATION_FAILED` | The tool ran but the result didn't check out (e.g. came out empty or unreadable) — this is a safety check catching a bug, not something you did wrong. If you can reproduce it, that's worth reporting. |
| `ENGINE_NOT_FOUND` | The local processing engine itself isn't set up correctly (a developer-setup issue, not a normal end-user error). |
| `ENGINE_ERROR` | Something unexpected went wrong internally. The specific cause isn't shown here (to avoid ever leaking document content into an error message) — check the app's logs if you need to debug further. |

If a tool needs Tesseract or LibreOffice and they're not installed, the
error will say so directly rather than failing silently — see the install
commands in the main [README](../README.md#running-it).
