import type { ComponentType } from "react";
import { CompareWorkspace } from "../features/compare/CompareWorkspace";
import { CompressWorkspace } from "../features/compress/CompressWorkspace";
import { CropWorkspace } from "../features/crop/CropWorkspace";
import { JpgToPdfWorkspace } from "../features/jpg-to-pdf/JpgToPdfWorkspace";
import { MergeWorkspace } from "../features/merge/MergeWorkspace";
import { OrganizeWorkspace } from "../features/organize/OrganizeWorkspace";
import { PageNumbersWorkspace } from "../features/page-numbers/PageNumbersWorkspace";
import { PdfAWorkspace } from "../features/pdf-a/PdfAWorkspace";
import { PdfToJpgWorkspace } from "../features/pdf-to-jpg/PdfToJpgWorkspace";
import { ProtectWorkspace } from "../features/protect/ProtectWorkspace";
import { RedactWorkspace } from "../features/redact/RedactWorkspace";
import { RepairWorkspace } from "../features/repair/RepairWorkspace";
import { RotateWorkspace } from "../features/rotate/RotateWorkspace";
import { ScanImportWorkspace } from "../features/scan-import/ScanImportWorkspace";
import { SignWorkspace } from "../features/sign/SignWorkspace";
import { SplitWorkspace } from "../features/split/SplitWorkspace";
import { UnlockWorkspace } from "../features/unlock/UnlockWorkspace";
import { WatermarkWorkspace } from "../features/watermark/WatermarkWorkspace";

interface WorkspaceProps {
  onBack: () => void;
}

const WORKSPACES: Record<string, ComponentType<WorkspaceProps>> = {
  merge: MergeWorkspace,
  split: SplitWorkspace,
  rotate: RotateWorkspace,
  organize: OrganizeWorkspace,
  compress: CompressWorkspace,
  watermark: WatermarkWorkspace,
  "page-numbers": PageNumbersWorkspace,
  "pdf-to-jpg": PdfToJpgWorkspace,
  "jpg-to-pdf": JpgToPdfWorkspace,
  crop: CropWorkspace,
  protect: ProtectWorkspace,
  unlock: UnlockWorkspace,
  repair: RepairWorkspace,
  redact: RedactWorkspace,
  sign: SignWorkspace,
  compare: CompareWorkspace,
  "pdf-a": PdfAWorkspace,
  "scan-import": ScanImportWorkspace,
};

interface ToolWorkspaceProps extends WorkspaceProps {
  toolId: string;
}

export function ToolWorkspace({ toolId, onBack }: ToolWorkspaceProps) {
  const Workspace = WORKSPACES[toolId];
  if (!Workspace) return null;
  return <Workspace onBack={onBack} />;
}
