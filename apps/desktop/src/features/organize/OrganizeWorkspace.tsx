import { useEffect, useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { PageThumbnailGrid, type ThumbnailItem } from "../../components/workspace/PageThumbnailGrid";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { useSingleFilePreview } from "../shared/useSingleFilePreview";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

export function OrganizeWorkspace({ onBack }: { onBack: () => void }) {
  const { inputPath, pageCount, thumbnails, loading, error, pickFile } = useSingleFilePreview();
  const [order, setOrder] = useState<ThumbnailItem[]>([]);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  // Thumbnails render asynchronously; keep `order` (the source of truth for
  // page order/removal) in sync as they arrive, without clobbering edits
  // the user already made to the order.
  useEffect(() => {
    setOrder((prev) => {
      if (prev.length === 0) {
        return thumbnails.map((thumbnail) => ({ page: thumbnail.page, thumbnail }));
      }
      return prev.map((item) => ({
        ...item,
        thumbnail: thumbnails.find((t) => t.page === item.page) ?? item.thumbnail,
      }));
    });
  }, [thumbnails]);

  function move(index: number, direction: -1 | 1) {
    setOrder((prev) => {
      const target = index + direction;
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function remove(index: number) {
    setOrder((prev) => prev.filter((_, i) => i !== index));
  }

  async function run() {
    if (!inputPath || !outputDir || order.length === 0) return;
    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "organize",
        inputs: [inputPath],
        options: { pageOrder: order.map((item) => item.page) },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!inputPath && !!outputDir && order.length > 0 && !running;

  return (
    <WorkspaceLayout title="Organize Pages" onBack={onBack}>
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

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Pages {pageCount > 0 && `(${order.length}/${pageCount} kept)`}
        </h2>
        <p className="text-xs text-slate-400">
          Hover a page to reorder (←/→) or remove it (✕).
        </p>
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Rendering previews…</p>
        ) : (
          <PageThumbnailGrid items={order} onMove={move} onRemove={remove} />
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
          Save organized PDF
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
