import { useEffect, useState } from "react";
import { deletePreset, listPresets, savePreset, type Preset } from "../../services/presets";

interface PresetControlsProps {
  tool: string;
  values: Record<string, unknown>;
  onLoad: (values: Record<string, unknown>) => void;
}

// Shared by Batch and Workflow Builder: both let the user pick a tool from
// PIPELINE_TOOLS and configure its flat options, so both can save/reload
// that same configuration as a named preset without duplicating this UI.
export function PresetControls({ tool, values, onLoad }: PresetControlsProps) {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [naming, setNaming] = useState(false);
  const [nameInput, setNameInput] = useState("");

  useEffect(() => {
    setSelectedId("");
    setNaming(false);
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tool]);

  async function refresh() {
    try {
      setPresets(await listPresets(tool));
    } catch {
      setPresets([]);
    }
  }

  async function handleSave() {
    if (!nameInput.trim()) return;
    await savePreset(nameInput.trim(), tool, values);
    setNameInput("");
    setNaming(false);
    refresh();
  }

  function handleLoad(id: string) {
    setSelectedId(id);
    const preset = presets.find((p) => p.id === id);
    if (preset) onLoad(preset.options);
  }

  async function handleDelete() {
    if (!selectedId) return;
    await deletePreset(selectedId);
    setSelectedId("");
    refresh();
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
      {presets.length > 0 && (
        <>
          <select
            value={selectedId}
            onChange={(e) => handleLoad(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="">Load preset…</option>
            {presets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          {selectedId && (
            <button type="button" onClick={handleDelete} className="text-red-600 hover:underline">
              Delete
            </button>
          )}
        </>
      )}

      {naming ? (
        <span className="flex items-center gap-1">
          <input
            autoFocus
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") setNaming(false);
            }}
            placeholder="Preset name"
            className="w-32 rounded-lg border border-slate-200 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
          />
          <button type="button" onClick={handleSave} className="hover:underline">
            Save
          </button>
        </span>
      ) : (
        <button type="button" onClick={() => setNaming(true)} className="hover:underline">
          Save as preset
        </button>
      )}
    </div>
  );
}
