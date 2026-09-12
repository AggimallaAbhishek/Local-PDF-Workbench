import type { ToolDefinition } from "../types/tool";

// Registry of every tool in the roadmap (PLAN.md §5). `available` flips to
// true as each tool's feature module + engine implementation lands.
export const TOOLS: ToolDefinition[] = [
  // MVP
  { id: "merge", name: "Merge PDF", description: "Combine multiple PDFs into one document.", category: "organize", stage: "mvp", available: true },
  { id: "split", name: "Split PDF", description: "Extract pages into separate documents.", category: "organize", stage: "mvp", available: true },
  { id: "rotate", name: "Rotate PDF", description: "Rotate one or more pages.", category: "organize", stage: "mvp", available: true },
  { id: "organize", name: "Organize Pages", description: "Reorder, insert, or remove pages.", category: "organize", stage: "mvp", available: true },
  { id: "compress", name: "Compress PDF", description: "Reduce file size with adjustable quality.", category: "optimize", stage: "mvp", available: true },
  { id: "watermark", name: "Add Watermark", description: "Stamp text or an image onto every page.", category: "edit", stage: "mvp", available: true },
  { id: "page-numbers", name: "Add Page Numbers", description: "Insert page numbers with custom position and style.", category: "edit", stage: "mvp", available: true },
  { id: "pdf-to-jpg", name: "PDF to JPG", description: "Export pages as JPG images.", category: "convert", stage: "mvp", available: true },
  { id: "jpg-to-pdf", name: "JPG to PDF", description: "Combine images into a single PDF.", category: "convert", stage: "mvp", available: true },

  // Phase 2
  { id: "annotate", name: "Edit & Annotate", description: "Add text, shapes, and comments.", category: "edit", stage: "phase2", available: false },
  { id: "redact", name: "Redact PDF", description: "Permanently remove sensitive content.", category: "security", stage: "phase2", available: true },
  { id: "crop", name: "Crop PDF", description: "Trim page margins.", category: "edit", stage: "phase2", available: true },
  { id: "repair", name: "Repair PDF", description: "Attempt to fix a damaged document.", category: "optimize", stage: "phase2", available: true },
  { id: "protect", name: "Protect PDF", description: "Encrypt with a password.", category: "security", stage: "phase2", available: true },
  { id: "unlock", name: "Unlock PDF", description: "Remove a password you already know.", category: "security", stage: "phase2", available: true },
  { id: "sign", name: "Sign PDF", description: "Add a signature to a document.", category: "security", stage: "phase2", available: true },
  { id: "compare", name: "Compare PDFs", description: "Highlight differences between two documents.", category: "edit", stage: "phase2", available: true },
  { id: "pdf-a", name: "Convert to PDF/A", description: "Prepare a document for long-term archiving.", category: "convert", stage: "phase2", available: true },
  { id: "scan-import", name: "Import Scan", description: "Turn a scanned image into a clean PDF.", category: "convert", stage: "phase2", available: true },

  // Phase 3
  { id: "pdf-to-word", name: "PDF to Word", description: "Convert to an editable DOCX file.", category: "convert", stage: "phase3", available: false },
  { id: "word-to-pdf", name: "Word to PDF", description: "Convert a DOCX file to PDF.", category: "convert", stage: "phase3", available: false },
  { id: "pdf-to-excel", name: "PDF to Excel", description: "Extract tables into XLSX.", category: "convert", stage: "phase3", available: false },
  { id: "excel-to-pdf", name: "Excel to PDF", description: "Convert an XLSX file to PDF.", category: "convert", stage: "phase3", available: false },
  { id: "pdf-to-ppt", name: "PDF to PowerPoint", description: "Convert to an editable PPTX file.", category: "convert", stage: "phase3", available: false },
  { id: "ppt-to-pdf", name: "PowerPoint to PDF", description: "Convert a PPTX file to PDF.", category: "convert", stage: "phase3", available: false },
  { id: "html-to-pdf", name: "HTML to PDF", description: "Render a local HTML file to PDF.", category: "convert", stage: "phase3", available: false },
  { id: "forms", name: "Fill Forms", description: "Fill and export PDF form fields.", category: "edit", stage: "phase3", available: false },
  { id: "ocr", name: "OCR PDF", description: "Make scanned pages searchable.", category: "intelligence", stage: "phase3", available: false },
  { id: "markdown", name: "Markdown to PDF", description: "Render Markdown as a formatted PDF.", category: "convert", stage: "phase3", available: false },

  // Advanced
  { id: "summarize", name: "Summarize Document", description: "Local summarization, no cloud calls.", category: "intelligence", stage: "advanced", available: false },
  { id: "translate", name: "Translate Document", description: "Offline translation.", category: "intelligence", stage: "advanced", available: false },
  { id: "workflow-builder", name: "Workflow Builder", description: "Chain tools into a multi-step pipeline.", category: "workflows", stage: "advanced", available: false },
  { id: "batch", name: "Batch Processing", description: "Run a tool across an entire folder.", category: "workflows", stage: "advanced", available: false },
  { id: "search", name: "Document Search", description: "Local full-text search across your PDFs.", category: "intelligence", stage: "advanced", available: false },
];

export const CATEGORIES: { id: ToolDefinition["category"] | "all"; label: string }[] = [
  { id: "all", label: "All Tools" },
  { id: "organize", label: "Organize" },
  { id: "optimize", label: "Optimize" },
  { id: "convert", label: "Convert" },
  { id: "edit", label: "Edit" },
  { id: "security", label: "Security" },
  { id: "intelligence", label: "Intelligence" },
  { id: "workflows", label: "Workflows" },
];
