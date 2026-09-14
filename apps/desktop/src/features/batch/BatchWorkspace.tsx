import { useState } from "react";
import { GenericOptionsForm } from "../../components/workspace/GenericOptionsForm";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { PresetControls } from "../../components/workspace/PresetControls";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { listFilesInDir, pickFolder } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";
import { PIPELINE_TOOLS, defaultFieldValues, findPipelineTool, toJobOptions } from "../shared/pipelineTools";

interface FileRun {
  path: string;
  status: "pending" | "running" | "success" | "error";
  message?: string;
}

function fileNameOf(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

export function BatchWorkspace({ onBack }: { onBack: () => void }) {
  const [toolId, setToolId] = useState(PIPELINE_TOOLS[0].id);
  const tool = findPipelineTool(toolId)!;
  const [fieldValues, setFieldValues] = useState<Record<string, unknown>>(defaultFieldValues(tool));
  const [inputDir, setInputDir] = useState<string | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [runs, setRuns] = useState<FileRun[]>([]);

  async function refreshFiles(dir: string, currentTool = tool) {
    setInputDir(dir);
    const found = await listFilesInDir(dir, currentTool.extensions);
    setFiles(found);
  }

  async function pickInputDir() {
    const dir = await pickFolder();
    if (dir) await refreshFiles(dir);
  }

  function handleToolChange(id: string) {
    const next = findPipelineTool(id)!;
    setToolId(id);
    setFieldValues(defaultFieldValues(next));
    if (inputDir) void refreshFiles(inputDir, next);
  }

  async function run() {
    if (files.length === 0 || !outputDir) return;
    setRunning(true);
    const initial: FileRun[] = files.map((path) => ({ path, status: "pending" }));
    setRuns(initial);

    const options = toJobOptions(tool, fieldValues);
    for (let i = 0; i < files.length; i++) {
      setRuns((prev) => prev.map((r, idx) => (idx === i ? { ...r, status: "running" } : r)));
      let outcome: FileRun;
      try {
        const result: JobResult = await runJob({
          jobId: crypto.randomUUID(),
          tool: tool.id,
          inputs: [files[i]],
          options,
          outputDir,
        });
        outcome =
          result.status === "success"
            ? { path: files[i], status: "success" }
            : { path: files[i], status: "error", message: result.error?.message };
      } catch (err) {
        outcome = { path: files[i], status: "error", message: err instanceof Error ? err.message : String(err) };
      }
      setRuns((prev) => prev.map((r, idx) => (idx === i ? outcome : r)));
    }
    setRunning(false);
  }

  const canRun = files.length > 0 && !!outputDir && !running;
  const succeeded = runs.filter((r) => r.status === "success").length;
  const failed = runs.filter((r) => r.status === "error").length;

  return (
    <WorkspaceLayout title="Batch Processing" onBack={onBack}>
      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Tool</h2>
        <select
          value={toolId}
          onChange={(e) => handleToolChange(e.target.value)}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          {PIPELINE_TOOLS.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
        <GenericOptionsForm fields={tool.fields} values={fieldValues} onChange={setFieldValues} />
        <PresetControls tool={toolId} values={fieldValues} onLoad={setFieldValues} />
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Input folder</h2>
          <button
            type="button"
            onClick={pickInputDir}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            {inputDir ? "Change folder" : "Choose folder"}
          </button>
        </div>
        {inputDir && (
          <p className="truncate text-sm text-slate-500 dark:text-slate-400">{inputDir}</p>
        )}
        <p className="text-xs text-slate-400">
          {inputDir
            ? `${files.length} matching file(s) (.${tool.extensions.join(", .")})`
            : "Choose a folder to see matching files."}
        </p>
      </section>

      {inputDir && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Output folder</h2>
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
          Run on {files.length} file(s)
        </button>
      </section>

      {runs.length > 0 && (
        <section className="space-y-2">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            {succeeded} succeeded, {failed} failed, {runs.length - succeeded - failed} remaining
          </p>
          <ul className="max-h-64 space-y-1 overflow-y-auto">
            {runs.map((r) => (
              <li key={r.path} className="flex items-center gap-2 text-sm">
                <span
                  className={
                    r.status === "success"
                      ? "text-emerald-600"
                      : r.status === "error"
                        ? "text-red-600"
                        : r.status === "running"
                          ? "text-slate-500"
                          : "text-slate-300"
                  }
                >
                  {r.status === "success" ? "✓" : r.status === "error" ? "✗" : r.status === "running" ? "…" : "·"}
                </span>
                <span className="min-w-0 flex-1 truncate text-slate-700 dark:text-slate-200">
                  {fileNameOf(r.path)}
                </span>
                {r.message && <span className="truncate text-xs text-red-500">{r.message}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </WorkspaceLayout>
  );
}
