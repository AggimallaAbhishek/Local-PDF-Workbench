import type { ReactNode } from "react";

interface WorkspaceLayoutProps {
  title: string;
  onBack: () => void;
  children: ReactNode;
}

export function WorkspaceLayout({ title, onBack, children }: WorkspaceLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
        <div className="mx-auto flex max-w-4xl items-center gap-3 px-6 py-4">
          <button
            type="button"
            onClick={onBack}
            className="rounded-lg border border-slate-300 px-2 py-1 text-sm text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            ← Back
          </button>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h1>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-6 py-8">{children}</main>
    </div>
  );
}
