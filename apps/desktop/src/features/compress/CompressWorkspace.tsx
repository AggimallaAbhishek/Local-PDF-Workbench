import { useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { pickInputFiles } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

const QUALITIES = ["low", "medium", "high"] as const;

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function CompressWorkspace({ onBack }: { onBack: () => void }) {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [quality, setQuality] = useState<(typeof QUALITIES)[number]>("medium");
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  async function pickFile() {
    const [path] = await pickInputFiles(false);
    if (path) setInputPath(path);
  }

  async function run() {
    if (!inputPath || !outputDir) return;
    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "compress",
        inputs: [inputPath],
        options: { quality },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!inputPath && !!outputDir && !running;

  const originalSize = result?.metadata?.originalSizeBytes as number | undefined;
  const compressedSize = result?.metadata?.compressedSizeBytes as number | undefined;

  return (
    <WorkspaceLayout title="Compress PDF" onBack={onBack}>
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
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Quality</h2>
        <div className="flex gap-4 text-sm text-slate-600 dark:text-slate-300">
          {QUALITIES.map((value) => (
            <label key={value} className="flex items-center gap-2 capitalize">
              <input type="radio" checked={quality === value} onChange={() => setQuality(value)} />
              {value}
            </label>
          ))}
        </div>
        <p className="text-xs text-slate-400">
          Lower quality shrinks embedded images more; text and vector content are unaffected.
        </p>
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
          Compress
        </button>
      </section>

      {result?.status === "success" && originalSize !== undefined && compressedSize !== undefined && (
        <p className="text-sm text-slate-600 dark:text-slate-300">
          {formatBytes(originalSize)} → {formatBytes(compressedSize)} (
          {Math.round((1 - compressedSize / originalSize) * 100)}% smaller)
        </p>
      )}

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
