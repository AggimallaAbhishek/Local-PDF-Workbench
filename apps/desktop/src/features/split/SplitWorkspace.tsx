import { useMemo, useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { PageThumbnailGrid } from "../../components/workspace/PageThumbnailGrid";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { useSingleFilePreview } from "../shared/useSingleFilePreview";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

type SplitMode = "everyPage" | "ranges";

function parseRanges(text: string, pageCount: number): { ranges: number[][]; pages: Set<number> } {
  const ranges: number[][] = [];
  const pages = new Set<number>();

  for (const part of text.split(",").map((p) => p.trim()).filter(Boolean)) {
    const [startRaw, endRaw] = part.split("-").map((n) => n.trim());
    const start = Number.parseInt(startRaw, 10);
    const end = endRaw ? Number.parseInt(endRaw, 10) : start;
    if (!Number.isInteger(start) || !Number.isInteger(end)) continue;
    if (start < 1 || end < start || end > pageCount) continue;

    ranges.push([start, end]);
    for (let p = start; p <= end; p++) pages.add(p);
  }

  return { ranges, pages };
}

export function SplitWorkspace({ onBack }: { onBack: () => void }) {
  const { inputPath, pageCount, thumbnails, loading, error, pickFile } = useSingleFilePreview();
  const [mode, setMode] = useState<SplitMode>("everyPage");
  const [rangesText, setRangesText] = useState("");
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  const { ranges, pages: selectedPages } = useMemo(
    () => parseRanges(rangesText, pageCount),
    [rangesText, pageCount],
  );

  const items = thumbnails.map((thumbnail) => ({
    page: thumbnail.page,
    thumbnail,
    selected: mode === "ranges" && selectedPages.has(thumbnail.page),
  }));

  async function run() {
    if (!inputPath || !outputDir) return;
    if (mode === "ranges" && ranges.length === 0) return;

    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "split",
        inputs: [inputPath],
        options: mode === "everyPage" ? { mode } : { mode, ranges },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun =
    !!inputPath && !!outputDir && !running && (mode === "everyPage" || ranges.length > 0);

  return (
    <WorkspaceLayout title="Split PDF" onBack={onBack}>
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Input</h2>
          <button
            type="button"
            onClick={pickFile}
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
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Options</h2>
          <div className="flex gap-4 text-sm text-slate-600 dark:text-slate-300">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={mode === "everyPage"}
                onChange={() => setMode("everyPage")}
              />
              One PDF per page
            </label>
            <label className="flex items-center gap-2">
              <input type="radio" checked={mode === "ranges"} onChange={() => setMode("ranges")} />
              Custom ranges
            </label>
          </div>
          {mode === "ranges" && (
            <input
              value={rangesText}
              onChange={(e) => setRangesText(e.target.value)}
              placeholder={`e.g. 1-3, 5, 7-${pageCount || 9}`}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            />
          )}
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Pages {pageCount > 0 && `(${pageCount})`}
        </h2>
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Rendering previews…</p>
        ) : (
          <PageThumbnailGrid items={items} />
        )}
      </section>

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
          Split
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
