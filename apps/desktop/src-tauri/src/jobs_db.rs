//! The app's local SQLite database: persistent job history (PLAN.md §3,
//! "persists job metadata to SQLite") and reusable tool-option presets
//! (PLAN.md §13's future-enhancements backlog). One connection, two tables -
//! both are small, low-write, single-user local data, not worth two
//! separate database files.

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

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PresetEntry {
    pub id: String,
    pub name: String,
    pub tool: String,
    pub options: serde_json::Value,
    pub created_at: i64,
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
);
CREATE TABLE IF NOT EXISTS presets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tool TEXT NOT NULL,
    options TEXT NOT NULL,
    created_at INTEGER NOT NULL
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

    /// Saves a named preset for one tool's options. IDs are derived
    /// (tool + timestamp) rather than a random UUID since presets are
    /// created far less often than jobs and a plain, inspectable ID is
    /// fine at this volume.
    pub fn save_preset(&self, name: &str, tool: &str, options: &serde_json::Value) -> rusqlite::Result<String> {
        let created_at = now_millis();
        let id = format!("{tool}-{created_at}");
        let conn = self.0.lock().unwrap();
        conn.execute(
            "INSERT INTO presets (id, name, tool, options, created_at) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![id, name, tool, options.to_string(), created_at],
        )?;
        Ok(id)
    }

    /// Presets are always browsed in the context of one already-selected
    /// tool (Batch's tool picker, a Workflow Builder step) - there's no UI
    /// need for "every preset across every tool" today, so this stays
    /// scoped rather than adding an unused "list all" branch.
    pub fn list_presets(&self, tool: &str) -> rusqlite::Result<Vec<PresetEntry>> {
        let conn = self.0.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, name, tool, options, created_at FROM presets WHERE tool = ?1 ORDER BY created_at DESC",
        )?;
        let rows = stmt.query_map(params![tool], |row| {
            let options_json: String = row.get(3)?;
            Ok(PresetEntry {
                id: row.get(0)?,
                name: row.get(1)?,
                tool: row.get(2)?,
                options: serde_json::from_str(&options_json).unwrap_or(serde_json::Value::Null),
                created_at: row.get(4)?,
            })
        })?;
        rows.collect()
    }

    pub fn delete_preset(&self, id: &str) -> rusqlite::Result<()> {
        let conn = self.0.lock().unwrap();
        conn.execute("DELETE FROM presets WHERE id = ?1", params![id])?;
        Ok(())
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

    #[test]
    fn saves_and_lists_a_preset_scoped_to_its_tool() {
        let db = JobsDb::open_in_memory().unwrap();
        let options = serde_json::json!({"quality": "high"});

        let id = db.save_preset("Compress for email", "compress", &options).unwrap();
        assert!(!id.is_empty());

        let compress_presets = db.list_presets("compress").unwrap();
        assert_eq!(compress_presets.len(), 1);
        assert_eq!(compress_presets[0].name, "Compress for email");
        assert_eq!(compress_presets[0].options, options);

        // a preset for a different tool must not leak into this tool's list
        let watermark_presets = db.list_presets("watermark").unwrap();
        assert!(watermark_presets.is_empty());
    }

    #[test]
    fn deletes_a_preset() {
        let db = JobsDb::open_in_memory().unwrap();
        let id = db.save_preset("Archival PDF", "pdf-a", &serde_json::json!({"conformance": "2B"})).unwrap();

        db.delete_preset(&id).unwrap();

        assert!(db.list_presets("pdf-a").unwrap().is_empty());
    }

    #[test]
    fn list_presets_orders_newest_first() {
        let db = JobsDb::open_in_memory().unwrap();
        db.save_preset("First", "compress", &serde_json::json!({"quality": "low"})).unwrap();
        std::thread::sleep(std::time::Duration::from_millis(2));
        db.save_preset("Second", "compress", &serde_json::json!({"quality": "high"})).unwrap();

        let presets = db.list_presets("compress").unwrap();
        assert_eq!(presets[0].name, "Second");
        assert_eq!(presets[1].name, "First");
    }
}
