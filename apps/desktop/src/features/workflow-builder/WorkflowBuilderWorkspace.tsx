import { appCacheDir, join } from "@tauri-apps/api/path";
import { useState } from "react";
import { GenericOptionsForm } from "../../components/workspace/GenericOptionsForm";
import { OutputDirField } from "../../components/workspace/OutputDirField";
import { PresetControls } from "../../components/workspace/PresetControls";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { pickInputFiles } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";
import { PIPELINE_TOOLS, defaultFieldValues, findPipelineTool, toJobOptions } from "../shared/pipelineTools";

interface Step {
  id: string;
  toolId: string;
  values: Record<string, unknown>;
}

function newStep(): Step {
  const tool = PIPELINE_TOOLS[0];
  return { id: crypto.randomUUID(), toolId: tool.id, values: defaultFieldValues(tool) };
}

async function scratchDir(): Promise<string> {
  const cache = await appCacheDir();
  return join(cache, "workflow-scratch");
}

export function WorkflowBuilderWorkspace({ onBack }: { onBack: () => void }) {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [steps, setSteps] = useState<Step[]>([newStep()]);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [runningStepIndex, setRunningStepIndex] = useState(-1);
  const [result, setResult] = useState<JobResult | null>(null);

  async function pickFile() {
    const [path] = await pickInputFiles(false);
    if (path) setInputPath(path);
  }

  function addStep() {
    setSteps((prev) => [...prev, newStep()]);
  }

  function removeStep(id: string) {
    setSteps((prev) => (prev.length > 1 ? prev.filter((s) => s.id !== id) : prev));
  }

  function moveStep(index: number, direction: -1 | 1) {
    setSteps((prev) => {
      const target = index + direction;
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function setStepTool(id: string, toolId: string) {
    const tool = findPipelineTool(toolId)!;
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, toolId, values: defaultFieldValues(tool) } : s)));
  }

  function setStepValues(id: string, values: Record<string, unknown>) {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, values } : s)));
  }

  async function run() {
    if (!inputPath || !outputDir) return;
    setRunning(true);
    setResult(null);
    const scratch = await scratchDir();

    let currentInput = inputPath;
    let finalResult: JobResult | null = null;

    try {
      for (let i = 0; i < steps.length; i++) {
        setRunningStepIndex(i);
        const step = steps[i];
        const tool = findPipelineTool(step.toolId)!;
        const isLastStep = i === steps.length - 1;

        const stepResult = await runJob({
          jobId: crypto.randomUUID(),
          tool: tool.id,
          inputs: [currentInput],
          options: toJobOptions(tool, step.values),
          outputDir: isLastStep ? outputDir : scratch,
        });

        if (stepResult.status !== "success") {
          finalResult = stepResult;
          break;
        }
        currentInput = stepResult.outputs[0];
        finalResult = stepResult;
      }
    } finally {
      setRunningStepIndex(-1);
      setRunning(false);
    }

    setResult(finalResult);
  }

  const canRun = !!inputPath && !!outputDir && steps.length > 0 && !running;

  return (
    <WorkspaceLayout title="Workflow Builder" onBack={onBack}>
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
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Steps (run in order)</h2>
          <button
            type="button"
            onClick={addStep}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Add step
          </button>
        </div>

        <ul className="space-y-3">
          {steps.map((step, index) => {
            const tool = findPipelineTool(step.toolId)!;
            return (
              <li
                key={step.id}
                className={`space-y-2 rounded-lg border p-3 ${
                  runningStepIndex === index
                    ? "border-slate-900 dark:border-slate-100"
                    : "border-slate-200 dark:border-slate-800"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">{index + 1}.</span>
                  <select
                    value={step.toolId}
                    onChange={(e) => setStepTool(step.id, e.target.value)}
                    className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
                  >
                    {PIPELINE_TOOLS.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => moveStep(index, -1)}
                    disabled={index === 0}
                    className="rounded px-1.5 text-slate-500 disabled:opacity-30"
                    aria-label="Move up"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    onClick={() => moveStep(index, 1)}
                    disabled={index === steps.length - 1}
                    className="rounded px-1.5 text-slate-500 disabled:opacity-30"
                    aria-label="Move down"
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    onClick={() => removeStep(step.id)}
                    disabled={steps.length === 1}
                    className="rounded px-1.5 text-red-600 disabled:opacity-30"
                    aria-label="Remove step"
                  >
                    ✕
                  </button>
                </div>
                <GenericOptionsForm
                  fields={tool.fields}
                  values={step.values}
                  onChange={(values) => setStepValues(step.id, values)}
                />
                <PresetControls
                  tool={step.toolId}
                  values={step.values}
                  onLoad={(values) => setStepValues(step.id, values)}
                />
              </li>
            );
          })}
        </ul>
        <p className="text-xs text-slate-400">
          Each step's output feeds the next step's input. If a step produces more than one file (e.g. PDF to
          JPG on a multi-page document), only the first continues down the chain.
        </p>
      </section>

      {inputPath && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Final output folder</h2>
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
          Run workflow
        </button>
      </section>

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
