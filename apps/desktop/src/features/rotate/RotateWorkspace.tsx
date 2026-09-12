import { useEffect, useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { PageThumbnailGrid } from "../../components/workspace/PageThumbnailGrid";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { useSingleFilePreview } from "../shared/useSingleFilePreview";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

const ANGLES = [90, 180, 270] as const;

export function RotateWorkspace({ onBack }: { onBack: () => void }) {
  const { inputPath, pageCount, thumbnails, loading, error, pickFile } = useSingleFilePreview();
  const [angle, setAngle] = useState<(typeof ANGLES)[number]>(90);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  // Default to "rotate everything" once pages load; the user can narrow it down.
  useEffect(() => {
    if (pageCount > 0) setSelected(new Set(Array.from({ length: pageCount }, (_, i) => i + 1)));
  }, [pageCount]);

  function toggle(page: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(page)) next.delete(page);
      else next.add(page);
      return next;
    });
  }

  const items = thumbnails.map((thumbnail) => ({
    page: thumbnail.page,
    thumbnail,
    selected: selected.has(thumbnail.page),
  }));

  async function run() {
    if (!inputPath || !outputDir || selected.size === 0) return;
    setRunning(true);
    setResult(null);
    try {
      const pages = selected.size === pageCount ? "all" : Array.from(selected).sort((a, b) => a - b);
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "rotate",
        inputs: [inputPath],
        options: { angle, pages },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!inputPath && !!outputDir && selected.size > 0 && !running;

  return (
    <WorkspaceLayout title="Rotate PDF" onBack={onBack}>
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
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Angle</h2>
          <div className="flex gap-4 text-sm text-slate-600 dark:text-slate-300">
            {ANGLES.map((value) => (
              <label key={value} className="flex items-center gap-2">
                <input type="radio" checked={angle === value} onChange={() => setAngle(value)} />
                {value}°
              </label>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Pages to rotate {pageCount > 0 && `(${selected.size}/${pageCount} selected)`}
          </h2>
          {pageCount > 0 && (
            <div className="flex gap-2 text-xs text-slate-500">
              <button
                type="button"
                onClick={() => setSelected(new Set(Array.from({ length: pageCount }, (_, i) => i + 1)))}
              >
                Select all
              </button>
              <button type="button" onClick={() => setSelected(new Set())}>
                Clear
              </button>
            </div>
          )}
        </div>
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Rendering previews…</p>
        ) : (
          <PageThumbnailGrid items={items} onToggle={toggle} />
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
          Rotate
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
