import type { ComponentType } from "react";
import { MergeWorkspace } from "../features/merge/MergeWorkspace";
import { OrganizeWorkspace } from "../features/organize/OrganizeWorkspace";
import { RotateWorkspace } from "../features/rotate/RotateWorkspace";
import { SplitWorkspace } from "../features/split/SplitWorkspace";

interface WorkspaceProps {
  onBack: () => void;
}

const WORKSPACES: Record<string, ComponentType<WorkspaceProps>> = {
  merge: MergeWorkspace,
  split: SplitWorkspace,
  rotate: RotateWorkspace,
  organize: OrganizeWorkspace,
};

interface ToolWorkspaceProps extends WorkspaceProps {
  toolId: string;
}

export function ToolWorkspace({ toolId, onBack }: ToolWorkspaceProps) {
  const Workspace = WORKSPACES[toolId];
  if (!Workspace) return null;
  return <Workspace onBack={onBack} />;
}
