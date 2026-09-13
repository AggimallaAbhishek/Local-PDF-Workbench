import { appCacheDir, join } from "@tauri-apps/api/path";
import { useState } from "react";
import { ResultPanel } from "../../components/workspace/ResultPanel";
import { WorkspaceLayout } from "../../components/workspace/WorkspaceLayout";
import { listFilesInDir, pickFolder } from "../../services/files";
import { runJob } from "../../services/engine";
import type { JobResult } from "../../types/job";

interface Match {
  file: string;
  page: number;
  snippet: string;
}

async function searchScratchDir(): Promise<string> {
  const cache = await appCacheDir();
  return join(cache, "search-results");
}

export function SearchWorkspace({ onBack }: { onBack: () => void }) {
  const [folder, setFolder] = useState<string | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<JobResult | null>(null);

  async function pickInputFolder() {
    const dir = await pickFolder();
    if (!dir) return;
    setFolder(dir);
    setFiles(await listFilesInDir(dir, ["pdf"]));
  }

  async function run() {
    if (files.length === 0 || !query.trim()) return;
    setRunning(true);
    setResult(null);
    try {
      const outputDir = await searchScratchDir();
      const jobResult = await runJob({
        jobId: crypto.randomUUID(),
        tool: "search",
        inputs: files,
        options: { query: query.trim(), caseSensitive },
        outputDir,
      });
      setResult(jobResult);
    } finally {
      setRunning(false);
    }
  }

  const canRun = files.length > 0 && !!query.trim() && !running;
  const matches = (result?.metadata?.matches as Match[] | undefined) ?? [];

  return (
    <WorkspaceLayout title="Document Search" onBack={onBack}>
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Folder</h2>
          <button
            type="button"
            onClick={pickInputFolder}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            {folder ? "Change folder" : "Choose folder"}
          </button>
        </div>
        {folder && <p className="truncate text-sm text-slate-500 dark:text-slate-400">{folder}</p>}
        <p className="text-xs text-slate-400">
          {folder ? `${files.length} PDF(s) found in this folder.` : "Choose a folder of PDFs to search."}
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-700 dark:text-slate-300">Query</h2>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Text to find"
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input type="checkbox" checked={caseSensitive} onChange={(e) => setCaseSensitive(e.target.checked)} />
          Case-sensitive
        </label>
      </section>

      <section>
        <button
          type="button"
          onClick={run}
          disabled={!canRun}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900"
        >
          Search
        </button>
      </section>

      {result?.status === "success" && (
        <section className="space-y-2">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            {result.metadata?.matchCount as number} match(es) across {result.metadata?.filesScanned as number} file(s)
          </p>
          <ul className="max-h-96 space-y-2 overflow-y-auto">
            {matches.map((m, i) => (
              <li
                key={`${m.file}-${m.page}-${i}`}
                className="rounded-lg border border-slate-200 p-2 text-sm dark:border-slate-800"
              >
                <p className="font-medium text-slate-700 dark:text-slate-200">
                  {m.file} — page {m.page}
                </p>
                <p className="text-slate-500 dark:text-slate-400">…{m.snippet}…</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <ResultPanel running={running} result={result} />
    </WorkspaceLayout>
  );
}
