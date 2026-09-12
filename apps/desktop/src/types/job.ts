// Job contract shared with the Python engine. Keep in sync with
// engine/jobs/contract.py — this is the single source of truth for the
// shape that crosses the Tauri <-> Python boundary.

export interface JobRequest {
  jobId: string;
  tool: string;
  inputs: string[];
  options: Record<string, unknown>;
  outputDir: string;
  overwriteOriginal?: boolean;
}

export type JobStatus = "success" | "error" | "cancelled";

export interface JobError {
  code: string;
  message: string;
}

export interface JobResult {
  jobId: string;
  status: JobStatus;
  outputs: string[];
  metadata?: Record<string, unknown>;
  warnings: string[];
  error?: JobError;
}
