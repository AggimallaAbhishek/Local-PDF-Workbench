import { PrivacyBadge } from "./PrivacyBadge";

interface TopNavProps {
  query: string;
  onQueryChange: (value: string) => void;
  version: string;
}

export function TopNav({ query, onQueryChange, version }: TopNavProps) {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-6 py-4">
        <div className="flex items-baseline gap-2">
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Local PDF Workbench
          </h1>
          <span className="text-xs text-slate-400">v{version}</span>
        </div>

        <input
          type="search"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search tools..."
          className="min-w-[200px] flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-900 outline-none focus:border-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        />

        <PrivacyBadge />
      </div>
    </header>
  );
}
