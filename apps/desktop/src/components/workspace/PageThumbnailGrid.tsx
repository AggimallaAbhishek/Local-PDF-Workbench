import type { PageThumbnail } from "../../services/preview";

export interface ThumbnailItem {
  page: number;
  thumbnail: PageThumbnail | undefined;
  selected?: boolean;
}

interface PageThumbnailGridProps {
  items: ThumbnailItem[];
  onToggle?: (page: number) => void;
  onMove?: (index: number, direction: -1 | 1) => void;
  onRemove?: (index: number) => void;
}

export function PageThumbnailGrid({ items, onToggle, onMove, onRemove }: PageThumbnailGridProps) {
  if (items.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-slate-400">
        Select a file to see its pages here.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-5">
      {items.map((item, index) => (
        <div
          key={`${item.page}-${index}`}
          onClick={onToggle ? () => onToggle(item.page) : undefined}
          className={`group relative flex flex-col items-center gap-1 rounded-lg border p-1.5 ${
            onToggle ? "cursor-pointer" : ""
          } ${
            item.selected
              ? "border-slate-900 ring-1 ring-slate-900 dark:border-slate-100 dark:ring-slate-100"
              : "border-slate-200 dark:border-slate-800"
          }`}
        >
          <div className="flex aspect-[3/4] w-full items-center justify-center overflow-hidden rounded bg-slate-100 dark:bg-slate-800">
            {item.thumbnail ? (
              <img
                src={item.thumbnail.src}
                alt={`Page ${item.page}`}
                className="h-full w-full object-contain"
              />
            ) : (
              <span className="text-xs text-slate-400">Loading…</span>
            )}
          </div>

          <span className="text-xs text-slate-500 dark:text-slate-400">Page {item.page}</span>

          {onMove && (
            <div className="absolute right-1 top-1 hidden gap-1 group-hover:flex">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onMove(index, -1);
                }}
                disabled={index === 0}
                className="rounded bg-white/90 px-1 text-xs shadow disabled:opacity-30 dark:bg-slate-900/90"
                aria-label="Move earlier"
              >
                ←
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onMove(index, 1);
                }}
                disabled={index === items.length - 1}
                className="rounded bg-white/90 px-1 text-xs shadow disabled:opacity-30 dark:bg-slate-900/90"
                aria-label="Move later"
              >
                →
              </button>
            </div>
          )}

          {onRemove && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(index);
              }}
              className="absolute left-1 top-1 hidden rounded bg-white/90 px-1 text-xs text-red-600 shadow group-hover:block dark:bg-slate-900/90"
              aria-label="Remove page"
            >
              ✕
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
