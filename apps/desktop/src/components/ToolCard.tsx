import type { ToolDefinition } from "../types/tool";

interface ToolCardProps {
  tool: ToolDefinition;
  onSelect: (tool: ToolDefinition) => void;
}

const STAGE_LABEL: Record<ToolDefinition["stage"], string> = {
  mvp: "MVP",
  phase2: "Phase 2",
  phase3: "Phase 3",
  advanced: "Advanced",
};

export function ToolCard({ tool, onSelect }: ToolCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(tool)}
      disabled={!tool.available}
      className="group flex flex-col items-start gap-2 rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex w-full items-start justify-between gap-2">
        <h3 className="font-medium text-slate-900 dark:text-slate-100">{tool.name}</h3>
        {!tool.available && (
          <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-400">
            {STAGE_LABEL[tool.stage]} · Coming soon
          </span>
        )}
      </div>
      <p className="text-sm text-slate-500 dark:text-slate-400">{tool.description}</p>
    </button>
  );
}
