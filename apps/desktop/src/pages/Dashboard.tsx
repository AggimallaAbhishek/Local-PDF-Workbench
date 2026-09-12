import { useMemo, useState } from "react";
import { TopNav } from "../components/TopNav";
import { CategoryFilters } from "../components/CategoryFilters";
import { ToolCard } from "../components/ToolCard";
import { TOOLS } from "../data/tools";
import type { ToolDefinition } from "../types/tool";

const APP_VERSION = "0.1.0";

interface DashboardProps {
  onSelectTool: (tool: ToolDefinition) => void;
}

export function Dashboard({ onSelectTool }: DashboardProps) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<ToolDefinition["category"] | "all">("all");

  const filteredTools = useMemo(() => {
    const q = query.trim().toLowerCase();
    return TOOLS.filter((tool) => {
      const matchesCategory = category === "all" || tool.category === category;
      const matchesQuery =
        q.length === 0 ||
        tool.name.toLowerCase().includes(q) ||
        tool.description.toLowerCase().includes(q);
      return matchesCategory && matchesQuery;
    });
  }, [query, category]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <TopNav query={query} onQueryChange={setQuery} version={APP_VERSION} />

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6 flex flex-col gap-4">
          <CategoryFilters active={category} onChange={setCategory} />
        </div>

        {filteredTools.length === 0 ? (
          <p className="py-16 text-center text-sm text-slate-400">
            No tools match "{query}".
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredTools.map((tool) => (
              <ToolCard key={tool.id} tool={tool} onSelect={onSelectTool} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
