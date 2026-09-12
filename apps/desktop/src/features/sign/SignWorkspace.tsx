import { useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { pickInputFiles, pickInputImages } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

export function SignWorkspace({ onBack }: { onBack: () => void }) {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [signaturePath, setSignaturePath] = useState<string | null>(null);
  const [page, setPage] = useState<number | "">("");
  const [x, setX] = useState(50);
  const [y, setY] = useState(50);
  const [width, setWidth] = useState(150);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  async function pickFile() {
    const [path] = await pickInputFiles(false);
    if (path) setInputPath(path);
  }

  async function pickSignature() {
    const [path] = await pickInputImages(false);
    if (path) setSignaturePath(path);
  }

  async function run() {
    if (!inputPath || !signaturePath || !outputDir) return;
    setRunning(true);
    setResult(null);
    try {
      const options: Record<string, unknown> = { imagePath: signaturePath, x, y, width };
      if (page !== "") options.page = page;
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "sign",
        inputs: [inputPath],
        options,
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!inputPath && !!signaturePath && !!outputDir && !running;

  return (
    <WorkspaceLayout title="Sign PDF" onBack={onBack}>
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Document</h2>
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
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Signature image</h2>
          <button
            type="button"
            onClick={pickSignature}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            {signaturePath ? "Change image" : "Choose image"}
          </button>
        </div>
        {signaturePath && (
          <p className="truncate text-sm text-slate-500 dark:text-slate-400">{signaturePath}</p>
        )}
        <p className="text-xs text-slate-400">
          A PNG with a transparent background works best. This stamps the image onto the page — it doesn't
          add a cryptographic digital signature.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Placement</h2>
        <div className="grid grid-cols-2 gap-3">
          <label className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
            Page
            <input
              type="number"
              min={1}
              value={page}
              onChange={(e) => setPage(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="last"
              className="w-20 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            />
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
            Width (pt)
            <input
              type="number"
              min={1}
              value={width}
              onChange={(e) => setWidth(Number(e.target.value))}
              className="w-20 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            />
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
            X (pt from left)
            <input
              type="number"
              min={0}
              value={x}
              onChange={(e) => setX(Number(e.target.value))}
              className="w-20 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            />
          </label>
          <label className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
            Y (pt from bottom)
            <input
              type="number"
              min={0}
              value={y}
              onChange={(e) => setY(Number(e.target.value))}
              className="w-20 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            />
          </label>
        </div>
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
          Sign
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
