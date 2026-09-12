export type ToolCategory =
  | "organize"
  | "optimize"
  | "convert"
  | "edit"
  | "security"
  | "intelligence"
  | "workflows";

export type ToolStage = "mvp" | "phase2" | "phase3" | "advanced";

export interface ToolDefinition {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  stage: ToolStage;
  /** False until the feature module + engine tool are implemented. */
  available: boolean;
}
