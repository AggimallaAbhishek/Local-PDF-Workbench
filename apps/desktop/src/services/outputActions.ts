import { invoke } from "@tauri-apps/api/core";

// Calls our own mediated Rust commands rather than the opener plugin's JS
// API directly: that plugin's open_path/reveal_item_in_dir have no scope
// mechanism at all, so granting them straight to the webview would let any
// frontend code act on an arbitrary path. See src-tauri/src/output.rs.

export function openOutputPath(path: string) {
  return invoke("open_output_path", { path });
}

export function revealOutputPath(path: string) {
  return invoke("reveal_output_path", { path });
}
