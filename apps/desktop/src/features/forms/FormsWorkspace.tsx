import { useState } from "react";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { pickInputFiles } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

interface FieldRow {
  id: string;
  name: string;
  value: string;
}

export function FormsWorkspace({ onBack }: { onBack: () => void }) {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [rows, setRows] = useState<FieldRow[]>([{ id: crypto.randomUUID(), name: "", value: "" }]);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  async function pickFile() {
    const [path] = await pickInputFiles(false);
    if (path) setInputPath(path);
  }

  function updateRow(id: string, patch: Partial<FieldRow>) {
    setRows((prev) => prev.map((row) => (row.id === id ? { ...row, ...patch } : row)));
  }

  function addRow() {
    setRows((prev) => [...prev, { id: crypto.randomUUID(), name: "", value: "" }]);
  }

  function removeRow(id: string) {
    setRows((prev) => (prev.length > 1 ? prev.filter((row) => row.id !== id) : prev));
  }

  async function run() {
    const fields = Object.fromEntries(
      rows.filter((row) => row.name.trim()).map((row) => [row.name.trim(), row.value]),
    );
    if (!inputPath || !outputDir || Object.keys(fields).length === 0) return;

    setRunning(true);
    setResult(null);
    try {
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "forms",
        inputs: [inputPath],
        options: { fields },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = !!inputPath && !!outputDir && rows.some((r) => r.name.trim()) && !running;
  const availableFields = result?.metadata?.availableFields as string[] | undefined;

  return (
    <WorkspaceLayout title="Fill Forms" onBack={onBack}>
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
          Field names must match the PDF's own form field names exactly. For checkboxes/radio buttons, use
          the "on" state name (often "/Yes") shown in the field's own properties.
        </p>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Field values</h2>
          <button
            type="button"
            onClick={addRow}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Add field
          </button>
        </div>
        <ul className="space-y-2">
          {rows.map((row) => (
            <li key={row.id} className="flex items-center gap-2">
              <input
                value={row.name}
                onChange={(e) => updateRow(row.id, { name: e.target.value })}
                placeholder="Field name"
                className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
              />
              <input
                value={row.value}
                onChange={(e) => updateRow(row.id, { value: e.target.value })}
                placeholder="Value"
                className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
              />
              <button
                type="button"
                onClick={() => removeRow(row.id)}
                disabled={rows.length === 1}
                className="rounded px-1.5 text-red-600 disabled:opacity-30"
                aria-label="Remove field"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
        {availableFields && (
          <p className="text-xs text-slate-400">
            This PDF's form fields: {availableFields.length ? availableFields.join(", ") : "(none found)"}
          </p>
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
          Fill Form
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
