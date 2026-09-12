//! Mediated file-open commands for job outputs.
//!
//! `tauri-plugin-opener`'s `open_path`/`reveal_item_in_dir` commands have no
//! scope mechanism at all - granting them directly to the webview lets any
//! JS in the frontend open or reveal an arbitrary filesystem path, with no
//! framework-level restriction (confirmed in the plugin's own permission
//! definitions: "Enables the ... command without any pre-configured scope").
//! That bypasses this app's own pattern of mediating privileged operations
//! through a validated Rust command (see `job.rs::run_job`), so these two
//! thin wrappers exist instead: capabilities/default.json grants JS access
//! to only these commands, not the raw plugin ones.

use std::path::Path;

#[tauri::command]
pub fn open_output_path(path: String) -> Result<(), String> {
    if !Path::new(&path).is_file() {
        return Err(format!("Refusing to open a path that is not an existing file: {path}"));
    }
    tauri_plugin_opener::open_path(&path, None::<&str>).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn reveal_output_path(path: String) -> Result<(), String> {
    if !Path::new(&path).is_file() {
        return Err(format!("Refusing to reveal a path that is not an existing file: {path}"));
    }
    tauri_plugin_opener::reveal_item_in_dir(&path).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    // Only the guard clause is tested here, not the success path: that path
    // launches a real OS app (Finder/Preview), which isn't something an
    // automated test should trigger as a side effect.

    #[test]
    fn open_output_path_rejects_nonexistent_path() {
        let result = open_output_path("/definitely/does/not/exist.pdf".to_string());
        assert!(result.is_err());
    }

    #[test]
    fn reveal_output_path_rejects_nonexistent_path() {
        let result = reveal_output_path("/definitely/does/not/exist.pdf".to_string());
        assert!(result.is_err());
    }

    #[test]
    fn open_output_path_rejects_a_directory() {
        // A directory exists but is_file() is false - reveal_item_in_dir
        // expects a file inside a directory, not the directory itself.
        let result = open_output_path(std::env::temp_dir().to_string_lossy().into_owned());
        assert!(result.is_err());
    }
}
