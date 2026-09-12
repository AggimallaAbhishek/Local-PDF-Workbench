import { useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { pickInputFiles } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

export function RepairWorkspace({ onBack }: { onBack: () => void }) {
  const [inputPath, setInputPath] = useState<string | null>(null);
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
        tool: "repair",
        inputs: [inputPath],
        options: {},
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!inputPath && !!outputDir && !running;

  return (
    <WorkspaceLayout title="Repair PDF" onBack={onBack}>
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
        <p className="text-xs text-slate-400">
          Attempts to rebuild a damaged document's structure. Severely corrupted files may not be recoverable.
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
          Repair
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
