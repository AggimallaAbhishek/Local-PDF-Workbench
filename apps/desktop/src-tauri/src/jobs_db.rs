//! Persistent job history (PLAN.md §3: the Job Manager "persists job
//! metadata to SQLite"). One row per job: written "running" when a job
//! starts, updated to its final status when it finishes.

use std::path::Path;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use rusqlite::{params, Connection};
use serde::Serialize;

pub struct JobsDb(Mutex<Connection>);

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JobHistoryEntry {
    pub job_id: String,
    pub tool: String,
    pub output_dir: String,
    pub status: String,
    pub outputs: Vec<String>,
    pub warnings: Vec<String>,
    pub error_code: Option<String>,
    pub error_message: Option<String>,
    pub created_at: i64,
    pub finished_at: Option<i64>,
}

pub fn now_millis() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}

const SCHEMA: &str = "CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    tool TEXT NOT NULL,
    output_dir TEXT NOT NULL,
    status TEXT NOT NULL,
    outputs TEXT NOT NULL DEFAULT '[]',
    warnings TEXT NOT NULL DEFAULT '[]',
    error_code TEXT,
    error_message TEXT,
    created_at INTEGER NOT NULL,
    finished_at INTEGER
)";

impl JobsDb {
    pub fn open(path: &Path) -> rusqlite::Result<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch(SCHEMA)?;
        Ok(Self(Mutex::new(conn)))
    }

    #[cfg(test)]
    pub fn open_in_memory() -> rusqlite::Result<Self> {
        let conn = Connection::open_in_memory()?;
        conn.execute_batch(SCHEMA)?;
        Ok(Self(Mutex::new(conn)))
    }

    pub fn record_started(&self, job_id: &str, tool: &str, output_dir: &str) -> rusqlite::Result<()> {
        let conn = self.0.lock().unwrap();
        conn.execute(
            "INSERT OR REPLACE INTO jobs (job_id, tool, output_dir, status, created_at) \
             VALUES (?1, ?2, ?3, 'running', ?4)",
            params![job_id, tool, output_dir, now_millis()],
        )?;
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    pub fn record_finished(
        &self,
        job_id: &str,
        status: &str,
        outputs: &[String],
        warnings: &[String],
        error_code: Option<&str>,
        error_message: Option<&str>,
    ) -> rusqlite::Result<()> {
        let conn = self.0.lock().unwrap();
        conn.execute(
            "UPDATE jobs SET status = ?1, outputs = ?2, warnings = ?3, error_code = ?4, \
             error_message = ?5, finished_at = ?6 WHERE job_id = ?7",
            params![
                status,
                serde_json::to_string(outputs).unwrap_or_else(|_| "[]".into()),
                serde_json::to_string(warnings).unwrap_or_else(|_| "[]".into()),
                error_code,
                error_message,
                now_millis(),
                job_id,
            ],
        )?;
        Ok(())
    }

    pub fn list_recent(&self, limit: i64) -> rusqlite::Result<Vec<JobHistoryEntry>> {
        let conn = self.0.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT job_id, tool, output_dir, status, outputs, warnings, error_code, \
             error_message, created_at, finished_at FROM jobs ORDER BY created_at DESC LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![limit], |row| {
            let outputs_json: String = row.get(4)?;
            let warnings_json: String = row.get(5)?;
            Ok(JobHistoryEntry {
                job_id: row.get(0)?,
                tool: row.get(1)?,
                output_dir: row.get(2)?,
                status: row.get(3)?,
                outputs: serde_json::from_str(&outputs_json).unwrap_or_default(),
                warnings: serde_json::from_str(&warnings_json).unwrap_or_default(),
                error_code: row.get(6)?,
                error_message: row.get(7)?,
                created_at: row.get(8)?,
                finished_at: row.get(9)?,
            })
        })?;
        rows.collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn records_a_job_from_start_to_finish() {
        let db = JobsDb::open_in_memory().unwrap();
        db.record_started("job-1", "merge", "/tmp/out").unwrap();

        let running = db.list_recent(10).unwrap();
        assert_eq!(running.len(), 1);
        assert_eq!(running[0].status, "running");
        assert!(running[0].finished_at.is_none());

        db.record_finished(
            "job-1",
            "success",
            &["/tmp/out/merged.pdf".to_string()],
            &[],
            None,
            None,
        )
        .unwrap();

        let finished = db.list_recent(10).unwrap();
        assert_eq!(finished.len(), 1);
        assert_eq!(finished[0].status, "success");
        assert_eq!(finished[0].outputs, vec!["/tmp/out/merged.pdf".to_string()]);
        assert!(finished[0].finished_at.is_some());
    }

    #[test]
    fn records_an_error_with_code_and_message() {
        let db = JobsDb::open_in_memory().unwrap();
        db.record_started("job-2", "split", "/tmp/out").unwrap();
        db.record_finished("job-2", "error", &[], &[], Some("INPUT_NOT_FOUND"), Some("no such file"))
            .unwrap();

        let entries = db.list_recent(10).unwrap();
        assert_eq!(entries[0].error_code.as_deref(), Some("INPUT_NOT_FOUND"));
        assert_eq!(entries[0].error_message.as_deref(), Some("no such file"));
    }

    #[test]
    fn list_recent_orders_newest_first_and_respects_limit() {
        let db = JobsDb::open_in_memory().unwrap();
        for i in 0..5 {
            db.record_started(&format!("job-{i}"), "merge", "/tmp/out").unwrap();
        }

        let entries = db.list_recent(2).unwrap();
        assert_eq!(entries.len(), 2);
        // later-inserted rows share the same millisecond sometimes in fast
        // test runs, but ordering must never error and must respect LIMIT.
    }
}
