import { CATEGORIES } from "../data/tools";
import type { ToolDefinition } from "../types/tool";

interface CategoryFiltersProps {
  active: ToolDefinition["category"] | "all";
  onChange: (category: ToolDefinition["category"] | "all") => void;
}

export function CategoryFilters({ active, onChange }: CategoryFiltersProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {CATEGORIES.map((category) => {
        const isActive = category.id === active;
        return (
          <button
            key={category.id}
            type="button"
            onClick={() => onChange(category.id)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
              isActive
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            }`}
          >
            {category.label}
          </button>
        );
      })}
    </div>
  );
}
