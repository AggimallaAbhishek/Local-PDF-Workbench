// Catalog of tools usable from Batch and Workflow Builder: both need "pick
// a tool, configure its options, run it on a file" and neither can host a
// bespoke options UI per tool the way a dedicated workspace does, so this
// is scoped to tools whose options are flat key/value pairs (a tool like
// crop, whose options nest under "margins", doesn't fit and is left out
// rather than special-cased).

export type FieldSpec =
  | { key: string; label: string; type: "text"; default: string }
  | { key: string; label: string; type: "number"; default: number; min?: number; max?: number }
  | { key: string; label: string; type: "select"; default: string; options: string[] };

export interface PipelineTool {
  id: string;
  label: string;
  /** Extensions (no leading dot) this tool accepts as input. */
  extensions: string[];
  fields: FieldSpec[];
}

export const PIPELINE_TOOLS: PipelineTool[] = [
  { id: "compress", label: "Compress PDF", extensions: ["pdf"], fields: [
    { key: "quality", label: "Quality", type: "select", default: "medium", options: ["low", "medium", "high"] },
  ] },
  { id: "repair", label: "Repair PDF", extensions: ["pdf"], fields: [] },
  { id: "rotate", label: "Rotate PDF (all pages)", extensions: ["pdf"], fields: [
    { key: "angle", label: "Angle", type: "select", default: "90", options: ["90", "180", "270"] },
  ] },
  { id: "protect", label: "Protect PDF", extensions: ["pdf"], fields: [
    { key: "password", label: "Password", type: "text", default: "" },
  ] },
  { id: "unlock", label: "Unlock PDF", extensions: ["pdf"], fields: [
    { key: "password", label: "Password", type: "text", default: "" },
  ] },
  { id: "redact", label: "Redact text", extensions: ["pdf"], fields: [
    { key: "text", label: "Text to remove", type: "text", default: "" },
  ] },
  { id: "watermark", label: "Add watermark", extensions: ["pdf"], fields: [
    { key: "text", label: "Watermark text", type: "text", default: "DRAFT" },
    { key: "opacity", label: "Opacity (0-1)", type: "number", default: 0.3, min: 0.05, max: 1 },
  ] },
  { id: "page-numbers", label: "Add page numbers", extensions: ["pdf"], fields: [
    {
      key: "position", label: "Position", type: "select", default: "bottom-center",
      options: ["bottom-center", "bottom-left", "bottom-right", "top-center", "top-left", "top-right"],
    },
  ] },
  { id: "pdf-a", label: "Convert to PDF/A", extensions: ["pdf"], fields: [
    { key: "conformance", label: "Conformance", type: "select", default: "2B", options: ["1B", "2B", "3B"] },
  ] },
  { id: "pdf-to-jpg", label: "PDF to JPG", extensions: ["pdf"], fields: [
    { key: "dpi", label: "DPI", type: "number", default: 150, min: 36, max: 600 },
  ] },
  { id: "ocr", label: "OCR PDF", extensions: ["pdf"], fields: [
    { key: "language", label: "Language", type: "text", default: "eng" },
    { key: "dpi", label: "DPI", type: "number", default: 300, min: 150, max: 600 },
  ] },
  { id: "word-to-pdf", label: "Word to PDF", extensions: ["doc", "docx"], fields: [] },
  { id: "excel-to-pdf", label: "Excel to PDF", extensions: ["xls", "xlsx"], fields: [] },
  { id: "ppt-to-pdf", label: "PowerPoint to PDF", extensions: ["ppt", "pptx"], fields: [] },
  { id: "html-to-pdf", label: "HTML to PDF", extensions: ["html", "htm"], fields: [] },
  { id: "markdown", label: "Markdown to PDF", extensions: ["md", "markdown"], fields: [] },
];

export function findPipelineTool(id: string): PipelineTool | undefined {
  return PIPELINE_TOOLS.find((t) => t.id === id);
}

export function defaultFieldValues(tool: PipelineTool): Record<string, unknown> {
  return Object.fromEntries(tool.fields.map((f) => [f.key, f.default]));
}

/** Converts raw field values into the JSON shape a job's `options` expects
 * (e.g. rotate's "angle" field is a string in the UI but a number for the
 * engine). Fields not needing conversion pass through unchanged. */
export function toJobOptions(tool: PipelineTool, values: Record<string, unknown>): Record<string, unknown> {
  const options: Record<string, unknown> = { ...values };
  if (tool.id === "rotate" && typeof options.angle === "string") {
    options.angle = Number(options.angle);
  }
  return options;
}
