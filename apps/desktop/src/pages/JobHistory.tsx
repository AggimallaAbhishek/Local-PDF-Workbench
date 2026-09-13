import { useEffect, useState } from "react";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { openOutputPath, revealOutputPath } from "../services/outputActions";
import { cancelJob, listJobHistory, type JobHistoryEntry } from "../services/jobs";

const POLL_INTERVAL_MS = 2000;

const STATUS_STYLES: Record<JobHistoryEntry["status"], string> = {
  running: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  error: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  cancelled: "bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
};

function formatTime(ms?: number): string {
  if (!ms) return "—";
  return new Date(ms).toLocaleString();
}

export function JobHistory({ onBack }: { onBack: () => void }) {
  const [jobs, setJobs] = useState<JobHistoryEntry[]>([]);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  async function refresh() {
    try {
      setJobs(await listJobHistory(100));
    } catch {
      // best-effort background refresh; keep showing the last good list
    }
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  async function handleCancel(jobId: string) {
    setCancellingId(jobId);
    try {
      await cancelJob(jobId);
    } finally {
      setCancellingId(null);
      refresh();
    }
  }

  return (
    <WorkspaceLayout title="Job History" onBack={onBack}>
      {jobs.length === 0 ? (
        <p className="py-16 text-center text-sm text-slate-400">No jobs have run yet.</p>
      ) : (
        <ul className="space-y-2">
          {jobs.map((job) => (
            <li
              key={job.jobId}
              className="space-y-2 rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{job.tool}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[job.status]}`}>
                    {job.status}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span>{formatTime(job.createdAt)}</span>
                  {job.status === "running" && (
                    <button
                      type="button"
                      onClick={() => handleCancel(job.jobId)}
                      disabled={cancellingId === job.jobId}
                      className="rounded-md border border-red-300 px-2 py-0.5 font-medium text-red-600 hover:bg-red-50 disabled:opacity-40 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950"
                    >
                      {cancellingId === job.jobId ? "Cancelling…" : "Cancel"}
                    </button>
                  )}
                </div>
              </div>

              {job.status === "error" && job.errorMessage && (
                <p className="text-xs text-red-600 dark:text-red-400">
                  {job.errorCode}: {job.errorMessage}
                </p>
              )}

              {job.outputs.length > 0 && (
                <ul className="space-y-1">
                  {job.outputs.map((path) => (
                    <li key={path} className="flex items-center justify-between gap-2 text-xs">
                      <span className="min-w-0 flex-1 truncate text-slate-500 dark:text-slate-400" title={path}>
                        {path}
                      </span>
                      <span className="flex shrink-0 gap-2">
                        <button
                          type="button"
                          onClick={() => openOutputPath(path)}
                          className="rounded border border-slate-300 px-1.5 py-0.5 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                        >
                          Open
                        </button>
                        <button
                          type="button"
                          onClick={() => revealOutputPath(path)}
                          className="rounded border border-slate-300 px-1.5 py-0.5 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                        >
                          Show in folder
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </WorkspaceLayout>
  );
}
