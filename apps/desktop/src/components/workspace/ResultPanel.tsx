import { openOutputPath, revealOutputPath } from "../../services/outputActions";
import type { JobResult } from "../../types/job";

interface ResultPanelProps {
  running: boolean;
  result: JobResult | null;
}

export function ResultPanel({ running, result }: ResultPanelProps) {
  if (running) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        Processing locally…
      </div>
    );
  }

  if (!result) return null;

  if (result.status === "error") {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
        <p className="font-medium">{result.error?.code ?? "ERROR"}</p>
        <p>{result.error?.message ?? "The job failed."}</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300">
      <p className="font-medium">Done</p>
      <ul className="mt-2 space-y-1">
        {result.outputs.map((path) => (
          <li key={path} className="flex items-center justify-between gap-3">
            <span className="truncate" title={path}>
              {path}
            </span>
            <span className="flex shrink-0 gap-2">
              <button
                type="button"
                onClick={() => openOutputPath(path)}
                className="rounded-md border border-emerald-300 px-2 py-0.5 text-xs font-medium hover:bg-emerald-100 dark:border-emerald-800 dark:hover:bg-emerald-900"
              >
                Open
              </button>
              <button
                type="button"
                onClick={() => revealOutputPath(path)}
                className="rounded-md border border-emerald-300 px-2 py-0.5 text-xs font-medium hover:bg-emerald-100 dark:border-emerald-800 dark:hover:bg-emerald-900"
              >
                Show in folder
              </button>
            </span>
          </li>
        ))}
      </ul>
      {result.warnings.length > 0 && (
        <ul className="mt-2 list-inside list-disc text-amber-700 dark:text-amber-400">
          {result.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
