import { invoke } from "@tauri-apps/api/core";
import type { JobRequest, JobResult } from "../types/job";

// Calls the Rust `run_job` command, which spawns the Python engine as a
// subprocess and returns its JobResult. See apps/desktop/src-tauri/src/job.rs.
export async function runJob(request: JobRequest): Promise<JobResult> {
  return invoke<JobResult>("run_job", { request });
}
