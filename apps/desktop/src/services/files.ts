import { open } from "@tauri-apps/plugin-dialog";

// Native pickers for a tool workspace's Input/Actions panels (see PLAN.md
// §6). Returns absolute local paths only — the UI never touches file bytes
// directly, it hands paths to `runJob` (see ./engine.ts).

export async function pickInputFiles(): Promise<string[]> {
  const selection = await open({
    multiple: true,
    directory: false,
    filters: [{ name: "PDF", extensions: ["pdf"] }],
  });
  if (selection === null) return [];
  return Array.isArray(selection) ? selection : [selection];
}

export async function pickOutputDir(): Promise<string | null> {
  const selection = await open({
    multiple: false,
    directory: true,
  });
  if (selection === null) return null;
  return Array.isArray(selection) ? (selection[0] ?? null) : selection;
}
