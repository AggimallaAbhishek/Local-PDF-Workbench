mod directory;
mod job;
mod jobs_db;
mod output;

use jobs_db::JobsDb;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;
            let db = JobsDb::open(&data_dir.join("jobs.db"))?;
            app.manage(db);
            app.manage(job::JobRegistry::default());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            job::run_job,
            job::cancel_job,
            job::list_jobs,
            output::open_output_path,
            output::reveal_output_path,
            directory::list_files_in_dir
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
