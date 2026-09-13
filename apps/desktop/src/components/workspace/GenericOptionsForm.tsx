import type { FieldSpec } from "../../features/shared/pipelineTools";

interface GenericOptionsFormProps {
  fields: FieldSpec[];
  values: Record<string, unknown>;
  onChange: (values: Record<string, unknown>) => void;
}

export function GenericOptionsForm({ fields, values, onChange }: GenericOptionsFormProps) {
  if (fields.length === 0) return null;

  function setField(key: string, value: unknown) {
    onChange({ ...values, [key]: value });
  }

  return (
    <div className="space-y-2">
      {fields.map((field) => (
        <label key={field.key} className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
          {field.label}
          {field.type === "select" ? (
            <select
              value={String(values[field.key] ?? field.default)}
              onChange={(e) => setField(field.key, e.target.value)}
              className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            >
              {field.options.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          ) : field.type === "number" ? (
            <input
              type="number"
              min={field.min}
              max={field.max}
              value={Number(values[field.key] ?? field.default)}
              onChange={(e) => setField(field.key, Number(e.target.value))}
              className="w-28 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            />
          ) : (
            <input
              value={String(values[field.key] ?? field.default)}
              onChange={(e) => setField(field.key, e.target.value)}
              className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            />
          )}
        </label>
      ))}
    </div>
  );
}
