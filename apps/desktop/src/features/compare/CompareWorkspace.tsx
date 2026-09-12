import { useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { pickInputFiles } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

export function CompareWorkspace({ onBack }: { onBack: () => void }) {
  const [pathA, setPathA] = useState<string | null>(null);
  const [pathB, setPathB] = useState<string | null>(null);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  async function pick(setter: (path: string) => void) {
    const [path] = await pickInputFiles(false);
    if (path) setter(path);
  }

  async function run() {
    if (!pathA || !pathB || !outputDir) return;
    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "compare",
        inputs: [pathA, pathB],
        options: {},
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!pathA && !!pathB && !!outputDir && !running;
  const differingPages = result?.metadata?.pagesWithDifferences as number[] | undefined;

  return (
    <WorkspaceLayout title="Compare PDFs" onBack={onBack}>
      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Documents</h2>
        {(
          [
            ["A", pathA, () => pick(setPathA)],
            ["B", pathB, () => pick(setPathB)],
          ] as const
        ).map(([label, path, onPick]) => (
          <div key={label} className="flex items-center gap-3">
            <span className="w-4 shrink-0 text-sm font-medium text-slate-500">{label}</span>
            <span className="min-w-0 flex-1 truncate rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
              {path ?? "No file selected"}
            </span>
            <button
              type="button"
              onClick={onPick}
              className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              Choose
            </button>
          </div>
        ))}
        <p className="text-xs text-slate-400">
          Compares extracted text page by page. Layout, image, and formatting differences aren't detected.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Output</h2>
        <OutputDirField outputDir={outputDir} onChange={setOutputDir} />
      </section>

      <section>
        <button
          type="button"
          onClick={run}
          disabled={!canRun}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900"
        >
          Compare
        </button>
      </section>

      {result?.status === "success" && differingPages !== undefined && (
        <p className="text-sm text-slate-600 dark:text-slate-300">
          {differingPages.length === 0
            ? "No differences found."
            : `${differingPages.length} page(s) differ: ${differingPages.join(", ")}`}
        </p>
      )}

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
