import { useRef, useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { runJob } from "../../services/engine";
import type { PageSize } from "../../services/preview";
import type { JobResult } from "../../types/job";
import { useSingleFilePreview } from "../shared/useSingleFilePreview";
import { screenPointToSvgPoint, toEngineOptions } from "./coordinates";
import type { Annotation, Tool } from "./types";

const COLORS = ["#e11d48", "#2563eb", "#16a34a", "#000000", "#f59e0b"];
const DEFAULT_PAGE_SIZE: PageSize = { width: 612, height: 792 }; // US Letter, used only before real sizes load
const MIN_DRAG_PX = 4;

type Draft =
  | { kind: "rectangle"; start: { x: number; y: number }; current: { x: number; y: number } }
  | { kind: "line"; start: { x: number; y: number }; current: { x: number; y: number } };

export function AnnotateWorkspace({ onBack }: { onBack: () => void }) {
  const { inputPath, pageCount, thumbnails, pageSizes, loading, error, pickFile } = useSingleFilePreview(900);
  const [currentPage, setCurrentPage] = useState(1);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [tool, setTool] = useState<Tool>("select");
  const [color, setColor] = useState(COLORS[0]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editingTextId, setEditingTextId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  async function handlePickFile() {
    await pickFile();
    setCurrentPage(1);
    setAnnotations([]);
    setSelectedId(null);
  }

  const thumbnail = thumbnails.find((t) => t.page === currentPage);
  const pageSize = pageSizes[currentPage] ?? DEFAULT_PAGE_SIZE;
  const pageAnnotations = annotations.filter((a) => a.page === currentPage);

  function addAnnotation(annotation: Annotation) {
    setAnnotations((prev) => [...prev, annotation]);
  }

  function commitTextEdit(id: string, value: string) {
    setEditingTextId(null);
    const trimmed = value.trim();
    if (!trimmed) {
      setAnnotations((prev) => prev.filter((a) => a.id !== id));
      return;
    }
    setAnnotations((prev) =>
      prev.map((a) => (a.id === id && a.type === "text" ? { ...a, text: trimmed } : a)),
    );
  }

  function deleteSelected() {
    if (!selectedId) return;
    setAnnotations((prev) => prev.filter((a) => a.id !== selectedId));
    setSelectedId(null);
  }

  function handleBackgroundClick() {
    if (tool === "select") setSelectedId(null);
  }

  function handlePointerDown(e: React.PointerEvent<SVGSVGElement>) {
    if (!svgRef.current || e.target !== svgRef.current) return; // a shape handles its own pointerdown
    const p = screenPointToSvgPoint(svgRef.current, e.clientX, e.clientY);

    if (tool === "text") {
      const id = crypto.randomUUID();
      addAnnotation({ id, type: "text", page: currentPage, x: p.x, y: p.y, text: "", fontSize: 16, color });
      setEditingTextId(id);
      setTool("select");
      return;
    }
    if (tool === "rectangle" || tool === "line") {
      setDraft({ kind: tool, start: p, current: p });
    }
  }

  function handlePointerMove(e: React.PointerEvent<SVGSVGElement>) {
    if (!draft || !svgRef.current) return;
    const p = screenPointToSvgPoint(svgRef.current, e.clientX, e.clientY);
    setDraft((prev) => (prev ? { ...prev, current: p } : prev));
  }

  function handlePointerUp() {
    if (!draft) return;
    const { kind, start, current } = draft;
    setDraft(null);

    if (kind === "rectangle") {
      const width = Math.abs(current.x - start.x);
      const height = Math.abs(current.y - start.y);
      if (width < MIN_DRAG_PX || height < MIN_DRAG_PX) return;
      addAnnotation({
        id: crypto.randomUUID(),
        type: "rectangle",
        page: currentPage,
        x: Math.min(start.x, current.x),
        y: Math.min(start.y, current.y),
        width,
        height,
        color,
      });
    } else {
      if (Math.hypot(current.x - start.x, current.y - start.y) < MIN_DRAG_PX) return;
      addAnnotation({
        id: crypto.randomUUID(),
        type: "line",
        page: currentPage,
        x1: start.x,
        y1: start.y,
        x2: current.x,
        y2: current.y,
        color,
      });
    }
  }

  function shapeHandlers(id: string) {
    return {
      onPointerDown: (e: React.PointerEvent) => e.stopPropagation(),
      onClick: (e: React.MouseEvent) => {
        e.stopPropagation();
        setSelectedId(id);
      },
    };
  }

  async function run() {
    if (!inputPath || !outputDir || annotations.length === 0) return;
    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "annotate",
        inputs: [inputPath],
        options: {
          annotations: annotations.map((a) => toEngineOptions(a, pageSizes[a.page] ?? DEFAULT_PAGE_SIZE)),
        },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!inputPath && !!outputDir && annotations.length > 0 && !running;

  return (
    <WorkspaceLayout title="Edit & Annotate" onBack={onBack}>
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Input</h2>
          <button
            type="button"
            onClick={handlePickFile}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            {inputPath ? "Change PDF" : "Choose PDF"}
          </button>
        </div>
        {inputPath && (
          <p className="truncate text-sm text-slate-500 dark:text-slate-400">{inputPath}</p>
        )}
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      </section>

      {inputPath && (
        <section className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            {(
              [
                ["select", "Select"],
                ["text", "Text"],
                ["rectangle", "Rectangle"],
                ["line", "Line"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => setTool(value)}
                className={`rounded-lg border px-3 py-1.5 text-sm font-medium ${
                  tool === value
                    ? "border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900"
                    : "border-slate-300 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                }`}
              >
                {label}
              </button>
            ))}

            <span className="mx-1 h-5 w-px bg-slate-200 dark:bg-slate-700" />

            {COLORS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                aria-label={`Color ${c}`}
                className={`h-6 w-6 rounded-full border-2 ${color === c ? "border-slate-900 dark:border-slate-100" : "border-transparent"}`}
                style={{ backgroundColor: c }}
              />
            ))}

            <span className="mx-1 h-5 w-px bg-slate-200 dark:bg-slate-700" />

            <button
              type="button"
              onClick={deleteSelected}
              disabled={!selectedId}
              className="rounded-lg border border-red-300 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-40 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950"
            >
              Delete selected
            </button>
          </div>

          <div className="flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-40 dark:border-slate-700"
            >
              ← Prev
            </button>
            <span>
              Page {currentPage} of {pageCount || "…"}
            </span>
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(pageCount, p + 1))}
              disabled={currentPage >= pageCount}
              className="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-40 dark:border-slate-700"
            >
              Next →
            </button>
          </div>

          {loading ? (
            <p className="py-16 text-center text-sm text-slate-400">Rendering pages…</p>
          ) : (
            <div className="relative mx-auto w-full max-w-xl overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
              {thumbnail && (
                <img src={thumbnail.src} alt={`Page ${currentPage}`} className="block w-full select-none" draggable={false} />
              )}
              <svg
                ref={svgRef}
                viewBox={`0 0 ${pageSize.width} ${pageSize.height}`}
                className="absolute inset-0 h-full w-full touch-none"
                style={{ cursor: tool === "select" ? "default" : "crosshair" }}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onClick={handleBackgroundClick}
              >
                {pageAnnotations.map((a) => {
                  if (a.type === "rectangle") {
                    return (
                      <g key={a.id}>
                        <rect
                          x={a.x}
                          y={a.y}
                          width={a.width}
                          height={a.height}
                          fill="none"
                          stroke={a.color}
                          strokeWidth={2}
                          {...shapeHandlers(a.id)}
                        />
                        {selectedId === a.id && (
                          <rect
                            x={a.x - 3}
                            y={a.y - 3}
                            width={a.width + 6}
                            height={a.height + 6}
                            fill="none"
                            stroke="#3b82f6"
                            strokeDasharray="4 3"
                          />
                        )}
                      </g>
                    );
                  }
                  if (a.type === "line") {
                    return (
                      <g key={a.id}>
                        <line x1={a.x1} y1={a.y1} x2={a.x2} y2={a.y2} stroke={a.color} strokeWidth={3} {...shapeHandlers(a.id)} />
                        {selectedId === a.id && (
                          <>
                            <circle cx={a.x1} cy={a.y1} r={5} fill="#3b82f6" />
                            <circle cx={a.x2} cy={a.y2} r={5} fill="#3b82f6" />
                          </>
                        )}
                      </g>
                    );
                  }
                  // text
                  if (editingTextId === a.id) {
                    return (
                      <foreignObject key={a.id} x={a.x} y={a.y} width={260} height={a.fontSize * 2.2}>
                        <input
                          autoFocus
                          defaultValue={a.text}
                          onBlur={(e) => commitTextEdit(a.id, e.currentTarget.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") e.currentTarget.blur();
                            if (e.key === "Escape") commitTextEdit(a.id, a.text);
                          }}
                          style={{
                            fontSize: a.fontSize,
                            border: "1px solid #3b82f6",
                            padding: "2px 4px",
                            width: "100%",
                            background: "white",
                            color: a.color,
                          }}
                        />
                      </foreignObject>
                    );
                  }
                  return (
                    <text
                      key={a.id}
                      x={a.x}
                      y={a.y + a.fontSize}
                      fontSize={a.fontSize}
                      fill={a.color}
                      onDoubleClick={() => setEditingTextId(a.id)}
                      {...shapeHandlers(a.id)}
                    >
                      {a.text}
                      {selectedId === a.id && (
                        <tspan dx={4} fontSize={a.fontSize * 0.7} fill="#3b82f6">
                          ✎
                        </tspan>
                      )}
                    </text>
                  );
                })}

                {draft?.kind === "rectangle" && (
                  <rect
                    x={Math.min(draft.start.x, draft.current.x)}
                    y={Math.min(draft.start.y, draft.current.y)}
                    width={Math.abs(draft.current.x - draft.start.x)}
                    height={Math.abs(draft.current.y - draft.start.y)}
                    fill="none"
                    stroke={color}
                    strokeDasharray="4 3"
                    strokeWidth={2}
                  />
                )}
                {draft?.kind === "line" && (
                  <line
                    x1={draft.start.x}
                    y1={draft.start.y}
                    x2={draft.current.x}
                    y2={draft.current.y}
                    stroke={color}
                    strokeDasharray="4 3"
                    strokeWidth={2}
                  />
                )}
              </svg>
            </div>
          )}
          <p className="text-xs text-slate-400">
            Double-click a text box to edit it. Click Select, then click a shape to select it for deletion.
          </p>
        </section>
      )}

      {inputPath && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Output</h2>
          <OutputDirField outputDir={outputDir} onChange={setOutputDir} />
        </section>
      )}

      <section>
        <button
          type="button"
          onClick={run}
          disabled={!canRun}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900"
        >
          Save annotated PDF
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
