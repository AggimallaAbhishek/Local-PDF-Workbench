import { invoke } from "@tauri-apps/api/core";

// Reusable tool-option presets (PLAN.md §13), scoped to one tool at a
// time - Batch's tool picker and each Workflow Builder step both browse
// presets for whichever tool is currently selected there.

export interface Preset {
  id: string;
  name: string;
  tool: string;
  options: Record<string, unknown>;
  createdAt: number;
}

export async function savePreset(name: string, tool: string, options: Record<string, unknown>): Promise<string> {
  return invoke<string>("save_preset", { name, tool, options });
}

export async function listPresets(tool: string): Promise<Preset[]> {
  return invoke<Preset[]>("list_presets", { tool });
}

export async function deletePreset(id: string): Promise<void> {
  return invoke("delete_preset", { id });
}
