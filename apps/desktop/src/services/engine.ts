import { invoke } from "@tauri-apps/api/core";
import type { JobRequest, JobResult } from "../types/job";

// Wired up in Sprint 2 once the `run_job` Tauri command and the Python
// engine subprocess runner exist. Kept here now so feature modules can be
// built against a stable interface.
export async function runJob(request: JobRequest): Promise<JobResult> {
  return invoke<JobResult>("run_job", { request });
}
