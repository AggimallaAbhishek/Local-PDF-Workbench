import { pickOutputDir } from "../../services/files";

interface OutputDirFieldProps {
  outputDir: string | null;
  onChange: (dir: string) => void;
}

export function OutputDirField({ outputDir, onChange }: OutputDirFieldProps) {
  async function handlePick() {
    const dir = await pickOutputDir();
    if (dir) onChange(dir);
  }

  return (
    <div className="flex items-center gap-3">
      <span className="min-w-0 flex-1 truncate rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
        {outputDir ?? "No output folder selected"}
      </span>
      <button
        type="button"
        onClick={handlePick}
        className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        Choose folder
      </button>
    </div>
  );
}
