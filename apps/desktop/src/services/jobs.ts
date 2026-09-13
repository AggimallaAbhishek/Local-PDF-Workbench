import { invoke } from "@tauri-apps/api/core";

// Wraps the Job Manager commands (PLAN.md §3): persisted job history and
// cancellation of a currently-running job. `runJob` itself lives in
// ./engine.ts — this file is for everything ELSE the Job Manager adds.

export interface JobHistoryEntry {
  jobId: string;
  tool: string;
  outputDir: string;
  status: "running" | "success" | "error" | "cancelled";
  outputs: string[];
  warnings: string[];
  errorCode?: string;
  errorMessage?: string;
  createdAt: number; // unix millis
  finishedAt?: number;
}

export async function listJobHistory(limit = 50): Promise<JobHistoryEntry[]> {
  return invoke<JobHistoryEntry[]>("list_jobs", { limit });
}

/** Returns true if a running job with this ID was found and killed. */
export async function cancelJob(jobId: string): Promise<boolean> {
  return invoke<boolean>("cancel_job", { jobId });
}
