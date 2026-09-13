import type { ComponentType } from "react";
import { SimpleConversionWorkspace } from "../components/workspace/SimpleConversionWorkspace";
import { AnnotateWorkspace } from "../features/annotate/AnnotateWorkspace";
import { BatchWorkspace } from "../features/batch/BatchWorkspace";
import { CompareWorkspace } from "../features/compare/CompareWorkspace";
import { CompressWorkspace } from "../features/compress/CompressWorkspace";
import { CropWorkspace } from "../features/crop/CropWorkspace";
import { FormsWorkspace } from "../features/forms/FormsWorkspace";
import { JpgToPdfWorkspace } from "../features/jpg-to-pdf/JpgToPdfWorkspace";
import { MergeWorkspace } from "../features/merge/MergeWorkspace";
import { OcrWorkspace } from "../features/ocr/OcrWorkspace";
import { OrganizeWorkspace } from "../features/organize/OrganizeWorkspace";
import { PageNumbersWorkspace } from "../features/page-numbers/PageNumbersWorkspace";
import { PdfAWorkspace } from "../features/pdf-a/PdfAWorkspace";
import { PdfToJpgWorkspace } from "../features/pdf-to-jpg/PdfToJpgWorkspace";
import { ProtectWorkspace } from "../features/protect/ProtectWorkspace";
import { RedactWorkspace } from "../features/redact/RedactWorkspace";
import { RepairWorkspace } from "../features/repair/RepairWorkspace";
import { RotateWorkspace } from "../features/rotate/RotateWorkspace";
import { ScanImportWorkspace } from "../features/scan-import/ScanImportWorkspace";
import { SearchWorkspace } from "../features/search/SearchWorkspace";
import { SignWorkspace } from "../features/sign/SignWorkspace";
import { SplitWorkspace } from "../features/split/SplitWorkspace";
import { SummarizeWorkspace } from "../features/summarize/SummarizeWorkspace";
import { TranslateWorkspace } from "../features/translate/TranslateWorkspace";
import { UnlockWorkspace } from "../features/unlock/UnlockWorkspace";
import { WatermarkWorkspace } from "../features/watermark/WatermarkWorkspace";
import { WorkflowBuilderWorkspace } from "../features/workflow-builder/WorkflowBuilderWorkspace";

interface WorkspaceProps {
  onBack: () => void;
}

const OFFICE_CONVERSION_LIMITATIONS =
  "Office conversions preserve most text and layout but may not match the original exactly.";

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
  annotate: AnnotateWorkspace,
  ocr: OcrWorkspace,
  forms: FormsWorkspace,
  "word-to-pdf": (props) => (
    <SimpleConversionWorkspace
      {...props}
      title="Word to PDF"
      tool="word-to-pdf"
      fileLabel="Word"
      fileExtensions={["doc", "docx"]}
      runLabel="Convert to PDF"
      helpText={OFFICE_CONVERSION_LIMITATIONS}
    />
  ),
  "excel-to-pdf": (props) => (
    <SimpleConversionWorkspace
      {...props}
      title="Excel to PDF"
      tool="excel-to-pdf"
      fileLabel="Excel"
      fileExtensions={["xls", "xlsx"]}
      runLabel="Convert to PDF"
      helpText={OFFICE_CONVERSION_LIMITATIONS}
    />
  ),
  "ppt-to-pdf": (props) => (
    <SimpleConversionWorkspace
      {...props}
      title="PowerPoint to PDF"
      tool="ppt-to-pdf"
      fileLabel="PowerPoint"
      fileExtensions={["ppt", "pptx"]}
      runLabel="Convert to PDF"
      helpText={OFFICE_CONVERSION_LIMITATIONS}
    />
  ),
  "html-to-pdf": (props) => (
    <SimpleConversionWorkspace
      {...props}
      title="HTML to PDF"
      tool="html-to-pdf"
      fileLabel="HTML"
      fileExtensions={["html", "htm"]}
      runLabel="Convert to PDF"
    />
  ),
  markdown: (props) => (
    <SimpleConversionWorkspace
      {...props}
      title="Markdown to PDF"
      tool="markdown"
      fileLabel="Markdown"
      fileExtensions={["md", "markdown"]}
      runLabel="Convert to PDF"
    />
  ),
  batch: BatchWorkspace,
  "workflow-builder": WorkflowBuilderWorkspace,
  search: SearchWorkspace,
  summarize: SummarizeWorkspace,
  translate: TranslateWorkspace,
};

interface ToolWorkspaceProps extends WorkspaceProps {
  toolId: string;
}

export function ToolWorkspace({ toolId, onBack }: ToolWorkspaceProps) {
  const Workspace = WORKSPACES[toolId];
  if (!Workspace) return null;
  return <Workspace onBack={onBack} />;
}
