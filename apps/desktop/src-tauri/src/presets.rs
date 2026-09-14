//! Save/load reusable tool-option presets (PLAN.md §13: "reusable presets
//! ('compress for email', 'prepare archival PDF')"). Scoped to tools whose
//! options are flat key/value JSON, matching the frontend's own
//! pipelineTools.ts catalog (used by Batch and Workflow Builder) - a
//! preset is just a named, saved copy of that same options shape.

use tauri::State;

use crate::jobs_db::{JobsDb, PresetEntry};

#[tauri::command]
pub fn save_preset(
    name: String,
    tool: String,
    options: serde_json::Value,
    db: State<'_, JobsDb>,
) -> Result<String, String> {
    if name.trim().is_empty() {
        return Err("Preset name must not be empty.".to_string());
    }
    db.save_preset(name.trim(), &tool, &options).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_presets(tool: String, db: State<'_, JobsDb>) -> Result<Vec<PresetEntry>, String> {
    db.list_presets(&tool).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_preset(id: String, db: State<'_, JobsDb>) -> Result<(), String> {
    db.delete_preset(&id).map_err(|e| e.to_string())
}
