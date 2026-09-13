import { useState } from "react";
import { pickFilesWithExtensions } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";
import { OutputDirField } from "./OutputDirField";
import { ResultPanel } from "./ResultPanel";
import { WorkspaceLayout } from "./WorkspaceLayout";

// Shared by every "one file in, no real options, one PDF out" conversion
// tool (word-to-pdf, excel-to-pdf, ppt-to-pdf, html-to-pdf, markdown) - the
// standards review flagged near-identical single-file workspaces as this
// codebase's main duplication risk, and these five are uniform enough to
// collapse into one parameterized component rather than five copies.
interface SimpleConversionWorkspaceProps {
  title: string;
  tool: string;
  fileLabel: string;
  fileExtensions: string[];
  runLabel: string;
  helpText?: string;
  onBack: () => void;
}

export function SimpleConversionWorkspace({
  title,
  tool,
  fileLabel,
  fileExtensions,
  runLabel,
  helpText,
  onBack,
}: SimpleConversionWorkspaceProps) {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  async function pickFile() {
    const [path] = await pickFilesWithExtensions(fileLabel, fileExtensions, false);
    if (path) setInputPath(path);
  }

  async function run() {
    if (!inputPath || !outputDir) return;
    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool,
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
    <WorkspaceLayout title={title} onBack={onBack}>
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Input</h2>
          <button
            type="button"
            onClick={pickFile}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            {inputPath ? "Change file" : `Choose ${fileLabel}`}
          </button>
        </div>
        {inputPath && (
          <p className="truncate text-sm text-slate-500 dark:text-slate-400">{inputPath}</p>
        )}
        {helpText && <p className="text-xs text-slate-400">{helpText}</p>}
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
          {runLabel}
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
