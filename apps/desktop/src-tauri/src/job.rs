//! `run_job` Tauri command: spawns the local Python engine as a one-shot
//! subprocess, sends it one JSON `JobRequest` on stdin, and parses the one
//! JSON `JobResult` it writes to stdout. Mirrors `engine/src/engine/jobs/contract.py`.
//!
//! Kept as request/response (no long-lived server) so a crashed or hung job
//! can never leak state into the next one — see `engine/src/engine/app/main.py`.
//!
//! The Job Manager pieces PLAN.md §3 calls for - job tracking/cancellation
//! and persisted history - live here (`JobRegistry`) and in `jobs_db.rs`:
//! every job is recorded "running" on start and updated to its final status
//! on finish, and a running job's OS process can be looked up by job ID and
//! killed via `cancel_job`.

use std::collections::{HashMap, HashSet};
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Mutex;

use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use tokio::io::AsyncWriteExt;
use tokio::process::Command;

use crate::jobs_db::JobsDb;

#[derive(Debug, Deserialize, Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct JobRequest {
    pub job_id: String,
    pub tool: String,
    pub inputs: Vec<String>,
    #[serde(default)]
    pub options: Map<String, Value>,
    pub output_dir: String,
    #[serde(default)]
    pub overwrite_original: bool,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JobError {
    pub code: String,
    pub message: String,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JobResult {
    pub job_id: String,
    pub status: String,
    #[serde(default)]
    pub outputs: Vec<String>,
    #[serde(default)]
    pub metadata: Map<String, Value>,
    #[serde(default)]
    pub warnings: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<JobError>,
}

impl JobResult {
    fn failed(job_id: &str, code: &str, message: impl Into<String>) -> Self {
        JobResult {
            job_id: job_id.to_string(),
            status: "error".to_string(),
            outputs: vec![],
            metadata: Map::new(),
            warnings: vec![],
            error: Some(JobError {
                code: code.to_string(),
                message: message.into(),
            }),
        }
    }

    fn cancelled(job_id: &str) -> Self {
        JobResult {
            job_id: job_id.to_string(),
            status: "cancelled".to_string(),
            outputs: vec![],
            metadata: Map::new(),
            warnings: vec![],
            error: None,
        }
    }
}

/// Tracks the OS process ID of every currently-running job, keyed by job
/// ID, so `cancel_job` can find and kill one. `cancelled` records which job
/// IDs were deliberately killed, so `run_job_impl` can tell "the user
/// cancelled this" apart from "the engine process crashed on its own" once
/// the (now-dead) child's exit status comes back either way.
#[derive(Default)]
pub struct JobRegistry {
    running_pids: Mutex<HashMap<String, u32>>,
    cancelled: Mutex<HashSet<String>>,
}

impl JobRegistry {
    fn register(&self, job_id: &str, pid: u32) {
        self.running_pids.lock().unwrap().insert(job_id.to_string(), pid);
    }

    fn unregister(&self, job_id: &str) {
        self.running_pids.lock().unwrap().remove(job_id);
    }

    /// Looks up the running job and kills its process. Returns false if no
    /// job with this ID is currently running (already finished, or never
    /// existed) - there is nothing to cancel in that case.
    pub fn cancel(&self, job_id: &str) -> bool {
        let pid = self.running_pids.lock().unwrap().get(job_id).copied();
        match pid {
            Some(pid) => {
                self.cancelled.lock().unwrap().insert(job_id.to_string());
                kill_process(pid);
                true
            }
            None => false,
        }
    }

    fn take_cancelled(&self, job_id: &str) -> bool {
        self.cancelled.lock().unwrap().remove(job_id)
    }
}

fn kill_process(pid: u32) {
    #[cfg(unix)]
    {
        let _ = std::process::Command::new("kill").arg("-9").arg(pid.to_string()).status();
    }
    #[cfg(windows)]
    {
        let _ = std::process::Command::new("taskkill")
            .args(["/F", "/PID", &pid.to_string()])
            .status();
    }
}

/// Resolves the engine's console-script entrypoint inside its venv.
///
/// Dev-only resolution: walks up from this crate to the repo root and into
/// `engine/.venv/bin/`. Packaging the engine as a Tauri sidecar binary (so
/// this doesn't depend on a checked-out venv) is Phase 5 hardening work,
/// tracked in PLAN.md, not part of Sprint 2.
fn engine_binary_path() -> Result<PathBuf, String> {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir
        .ancestors()
        .nth(3)
        .ok_or_else(|| "could not resolve repo root from CARGO_MANIFEST_DIR".to_string())?;

    let bin_name = if cfg!(windows) {
        "local-pdf-workbench-engine.exe"
    } else {
        "local-pdf-workbench-engine"
    };
    let venv_subdir = if cfg!(windows) { "Scripts" } else { "bin" };

    let path = repo_root
        .join("engine")
        .join(".venv")
        .join(venv_subdir)
        .join(bin_name);

    if !path.exists() {
        return Err(format!(
            "engine venv not found at {} — run `uv sync` inside engine/",
            path.display()
        ));
    }

    Ok(path)
}

fn record_finish(db: &JobsDb, result: JobResult) -> JobResult {
    let _ = db.record_finished(
        &result.job_id,
        &result.status,
        &result.outputs,
        &result.warnings,
        result.error.as_ref().map(|e| e.code.as_str()),
        result.error.as_ref().map(|e| e.message.as_str()),
    );
    result
}

pub async fn run_job_impl(request: JobRequest, registry: &JobRegistry, db: &JobsDb) -> JobResult {
    let job_id = request.job_id.clone();
    let _ = db.record_started(&job_id, &request.tool, &request.output_dir);

    let bin = match engine_binary_path() {
        Ok(path) => path,
        Err(message) => return record_finish(db, JobResult::failed(&job_id, "ENGINE_NOT_FOUND", message)),
    };

    let payload = match serde_json::to_vec(&request) {
        Ok(payload) => payload,
        Err(e) => {
            return record_finish(
                db,
                JobResult::failed(&job_id, "ENGINE_ERROR", format!("failed to serialize job request: {e}")),
            )
        }
    };

    let mut child = match Command::new(&bin)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(e) => {
            return record_finish(
                db,
                JobResult::failed(&job_id, "ENGINE_SPAWN_FAILED", format!("failed to start engine process: {e}")),
            )
        }
    };

    if let Some(mut stdin) = child.stdin.take() {
        if let Err(e) = stdin.write_all(&payload).await {
            return record_finish(
                db,
                JobResult::failed(&job_id, "ENGINE_IO_ERROR", format!("failed to write job request to engine stdin: {e}")),
            );
        }
        // stdin dropped here, closing it - signals EOF to the child so it stops reading.
    }

    if let Some(pid) = child.id() {
        registry.register(&job_id, pid);
    }

    let output = child.wait_with_output().await;
    registry.unregister(&job_id);
    let was_cancelled = registry.take_cancelled(&job_id);

    let output = match output {
        Ok(output) => output,
        Err(e) => {
            return record_finish(
                db,
                JobResult::failed(&job_id, "ENGINE_IO_ERROR", format!("failed to read engine output: {e}")),
            )
        }
    };

    if was_cancelled {
        return record_finish(db, JobResult::cancelled(&job_id));
    }

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return record_finish(
            db,
            JobResult::failed(
                &job_id,
                "ENGINE_PROCESS_FAILED",
                if stderr.is_empty() {
                    format!("engine process exited with status {}", output.status)
                } else {
                    stderr
                },
            ),
        );
    }

    let result = match serde_json::from_slice::<JobResult>(&output.stdout) {
        Ok(result) => result,
        Err(e) => JobResult::failed(&job_id, "ENGINE_BAD_RESPONSE", format!("engine returned invalid JSON: {e}")),
    };
    record_finish(db, result)
}

#[tauri::command]
pub async fn run_job(
    request: JobRequest,
    registry: tauri::State<'_, JobRegistry>,
    db: tauri::State<'_, JobsDb>,
) -> Result<JobResult, String> {
    Ok(run_job_impl(request, &registry, &db).await)
}

#[tauri::command]
pub fn cancel_job(job_id: String, registry: tauri::State<'_, JobRegistry>) -> bool {
    registry.cancel(&job_id)
}

#[tauri::command]
pub fn list_jobs(
    db: tauri::State<'_, JobsDb>,
    limit: Option<i64>,
) -> Result<Vec<crate::jobs_db::JobHistoryEntry>, String> {
    db.list_recent(limit.unwrap_or(50)).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::jobs_db::JobsDb;

    /// End-to-end check against the real dev venv: an unregistered tool
    /// must round-trip through the subprocess as a structured error, not
    /// a crash or a raw exception string. This is the Sprint 2 exit
    /// criterion ("one working end-to-end local job pipeline") made concrete.
    #[test]
    fn unknown_tool_round_trips_as_structured_error() {
        if engine_binary_path().is_err() {
            eprintln!("skipping: engine venv not present (run `uv sync` in engine/)");
            return;
        }

        let request = JobRequest {
            job_id: "test-job-1".to_string(),
            tool: "does-not-exist".to_string(),
            inputs: vec![],
            options: Map::new(),
            output_dir: "/tmp".to_string(),
            overwrite_original: false,
        };

        let registry = JobRegistry::default();
        let db = JobsDb::open_in_memory().expect("in-memory db should open");
        let result = tauri::async_runtime::block_on(run_job_impl(request, &registry, &db));

        assert_eq!(result.job_id, "test-job-1");
        assert_eq!(result.status, "error");
        assert_eq!(result.error.unwrap().code, "TOOL_NOT_IMPLEMENTED");

        let history = db.list_recent(10).expect("history should be readable");
        assert_eq!(history.len(), 1);
        assert_eq!(history[0].status, "error");
        assert_eq!(history[0].error_code.as_deref(), Some("TOOL_NOT_IMPLEMENTED"));
    }

    #[test]
    fn registry_reports_no_job_to_cancel_when_none_is_running() {
        let registry = JobRegistry::default();
        assert!(!registry.cancel("no-such-job"));
    }

    #[test]
    fn registry_forgets_a_job_once_unregistered() {
        let registry = JobRegistry::default();
        registry.register("job-x", 999_999); // a pid unlikely to be real
        registry.unregister("job-x");
        assert!(!registry.cancel("job-x"), "cancel must not find a job after it's unregistered");
    }

    #[cfg(unix)]
    #[test]
    fn cancel_actually_terminates_a_running_process() {
        let registry = JobRegistry::default();

        let mut child = tauri::async_runtime::block_on(async {
            tokio::process::Command::new("sleep")
                .arg("30")
                .spawn()
                .expect("failed to spawn sleep")
        });
        let pid = child.id().expect("spawned child should have a pid");
        registry.register("cancel-test-job", pid);

        assert!(registry.cancel("cancel-test-job"), "cancel() should find and kill the registered job");

        let status = tauri::async_runtime::block_on(child.wait()).expect("wait should succeed after kill");
        assert!(!status.success(), "a killed process must not report a successful exit");
        assert!(
            registry.take_cancelled("cancel-test-job"),
            "the job must be marked cancelled so run_job_impl reports status \"cancelled\", not an error"
        );
    }
}
