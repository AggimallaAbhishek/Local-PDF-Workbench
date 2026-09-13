//! Lists files in a folder the user picked via the native dialog picker.
//!
//! Batch, Workflow Builder, and Search all need to turn "a folder" into
//! "the PDFs in it" before building job requests. This is a plain Rust
//! command (like `job::run_job` and `output::open_output_path`), so it
//! needs no new Tauri plugin or capability grant - only app-defined
//! commands invoked directly from JS go through the ACL, not Rust code
//! calling `std::fs` itself.

use std::fs;
use std::path::Path;

#[tauri::command]
pub fn list_files_in_dir(dir: String, extensions: Vec<String>) -> Result<Vec<String>, String> {
    let dir_path = Path::new(&dir);
    if !dir_path.is_dir() {
        return Err(format!("Not a directory: {dir}"));
    }

    let lower_extensions: Vec<String> = extensions.iter().map(|e| e.to_lowercase()).collect();
    let entries = fs::read_dir(dir_path).map_err(|e| e.to_string())?;

    let mut files: Vec<String> = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let matches = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| lower_extensions.contains(&ext.to_lowercase()))
            .unwrap_or(false);
        if matches {
            files.push(path.to_string_lossy().into_owned());
        }
    }

    files.sort();
    Ok(files)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_a_path_that_is_not_a_directory() {
        let result = list_files_in_dir("/definitely/does/not/exist".to_string(), vec!["pdf".to_string()]);
        assert!(result.is_err());
    }

    #[test]
    fn filters_by_extension_case_insensitively_and_sorts() {
        let dir = std::env::temp_dir().join(format!("lpw-dirtest-{}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        fs::write(dir.join("b.PDF"), b"x").unwrap();
        fs::write(dir.join("a.pdf"), b"x").unwrap();
        fs::write(dir.join("c.txt"), b"x").unwrap();

        let result = list_files_in_dir(dir.to_string_lossy().into_owned(), vec!["pdf".to_string()]).unwrap();

        assert_eq!(result.len(), 2);
        assert!(result[0].ends_with("a.pdf"));
        assert!(result[1].ends_with("b.PDF"));

        fs::remove_dir_all(&dir).ok();
    }
}
