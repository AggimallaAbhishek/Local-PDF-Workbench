import { useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { pickInputFiles } from "../../services/files";
import { runJob } from "../../services/engine";
import { renderPageThumbnails, type PageThumbnail } from "../../services/preview";
import type { JobResult } from "../../types/job";

interface FileEntry {
  path: string;
  name: string;
  thumbnail?: PageThumbnail;
}

function fileNameOf(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

export function MergeWorkspace({ onBack }: { onBack: () => void }) {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [outputName, setOutputName] = useState("merged.pdf");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  async function addFiles() {
    const paths = await pickInputFiles();
    const additions = paths.filter((p) => !files.some((f) => f.path === p));
    if (additions.length === 0) return;

    const entries: FileEntry[] = additions.map((path) => ({ path, name: fileNameOf(path) }));
    setFiles((prev) => [...prev, ...entries]);

    for (const entry of entries) {
      try {
        const { thumbnails } = await renderPageThumbnails(entry.path, [1]);
        setFiles((prev) =>
          prev.map((f) => (f.path === entry.path ? { ...f, thumbnail: thumbnails[0] } : f)),
        );
      } catch {
        // a missing thumbnail doesn't block merging
      }
    }
  }

  function move(index: number, direction: -1 | 1) {
    setFiles((prev) => {
      const target = index + direction;
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function remove(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function run() {
    if (files.length < 2 || !outputDir) return;
    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "merge",
        inputs: files.map((f) => f.path),
        options: { outputFilename: outputName },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = files.length >= 2 && !!outputDir && !running;

  return (
    <WorkspaceLayout title="Merge PDF" onBack={onBack}>
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Files (in merge order)
          </h2>
          <button
            type="button"
            onClick={addFiles}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Add PDFs
          </button>
        </div>

        {files.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">
            Add at least two PDFs to merge.
          </p>
        ) : (
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li
                key={file.path}
                className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="flex h-14 w-11 shrink-0 items-center justify-center overflow-hidden rounded bg-slate-100 dark:bg-slate-800">
                  {file.thumbnail ? (
                    <img src={file.thumbnail.src} alt="" className="h-full w-full object-contain" />
                  ) : (
                    <span className="text-[10px] text-slate-400">…</span>
                  )}
                </div>
                <span className="min-w-0 flex-1 truncate text-sm text-slate-700 dark:text-slate-200">
                  {file.name}
                </span>
                <button
                  type="button"
                  onClick={() => move(index, -1)}
                  disabled={index === 0}
                  className="rounded px-1.5 text-slate-500 disabled:opacity-30"
                  aria-label="Move up"
                >
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => move(index, 1)}
                  disabled={index === files.length - 1}
                  className="rounded px-1.5 text-slate-500 disabled:opacity-30"
                  aria-label="Move down"
                >
                  ↓
                </button>
                <button
                  type="button"
                  onClick={() => remove(index)}
                  className="rounded px-1.5 text-red-600"
                  aria-label="Remove"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Options</h2>
        <label className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
          Output filename
          <input
            value={outputName}
            onChange={(e) => setOutputName(e.target.value)}
            className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
          />
        </label>
        <OutputDirField outputDir={outputDir} onChange={setOutputDir} />
      </section>

      <section>
        <button
          type="button"
          onClick={run}
          disabled={!canRun}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900"
        >
          Merge
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
