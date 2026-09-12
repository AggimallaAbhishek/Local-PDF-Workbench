//! `run_job` Tauri command: spawns the local Python engine as a one-shot
//! subprocess, sends it one JSON `JobRequest` on stdin, and parses the one
//! JSON `JobResult` it writes to stdout. Mirrors `engine/src/engine/jobs/contract.py`.
//!
//! Kept as request/response (no long-lived server) so a crashed or hung job
//! can never leak state into the next one — see `engine/src/engine/app/main.py`.

use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};

#[derive(Debug, Deserialize, Serialize)]
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

#[tauri::command]
pub fn run_job(request: JobRequest) -> Result<JobResult, String> {
    let job_id = request.job_id.clone();

    let bin = match engine_binary_path() {
        Ok(path) => path,
        Err(message) => return Ok(JobResult::failed(&job_id, "ENGINE_NOT_FOUND", message)),
    };

    let payload = serde_json::to_vec(&request)
        .map_err(|e| format!("failed to serialize job request: {e}"))?;

    let mut child = match Command::new(&bin)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(e) => {
            return Ok(JobResult::failed(
                &job_id,
                "ENGINE_SPAWN_FAILED",
                format!("failed to start engine process: {e}"),
            ))
        }
    };

    if let Some(mut stdin) = child.stdin.take() {
        if let Err(e) = stdin.write_all(&payload) {
            return Ok(JobResult::failed(
                &job_id,
                "ENGINE_IO_ERROR",
                format!("failed to write job request to engine stdin: {e}"),
            ));
        }
    }

    let output = match child.wait_with_output() {
        Ok(output) => output,
        Err(e) => {
            return Ok(JobResult::failed(
                &job_id,
                "ENGINE_IO_ERROR",
                format!("failed to read engine output: {e}"),
            ))
        }
    };

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Ok(JobResult::failed(
            &job_id,
            "ENGINE_PROCESS_FAILED",
            if stderr.is_empty() {
                format!("engine process exited with status {}", output.status)
            } else {
                stderr
            },
        ));
    }

    match serde_json::from_slice::<JobResult>(&output.stdout) {
        Ok(result) => Ok(result),
        Err(e) => Ok(JobResult::failed(
            &job_id,
            "ENGINE_BAD_RESPONSE",
            format!("engine returned invalid JSON: {e}"),
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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

        let result = run_job(request).expect("run_job should not error for a known bad tool");
        assert_eq!(result.job_id, "test-job-1");
        assert_eq!(result.status, "error");
        assert_eq!(result.error.unwrap().code, "TOOL_NOT_IMPLEMENTED");
    }
}
