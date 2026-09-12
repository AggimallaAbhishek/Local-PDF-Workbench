mod job;
mod output;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            job::run_job,
            output::open_output_path,
            output::reveal_output_path
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
