import { useState } from "react";
import { pickInputFiles } from "../../services/files";
import { renderPageThumbnails, type PageSize, type PageThumbnail } from "../../services/preview";

// Shared by split/rotate/organize/annotate: each operates on exactly one
// input PDF and needs its page thumbnails for a selection, reorder, or
// editing UI. `maxWidthPx` defaults to preview's own default (240px);
// annotate requests a larger render for editing precision.
export function useSingleFilePreview(maxWidthPx?: number) {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [thumbnails, setThumbnails] = useState<PageThumbnail[]>([]);
  const [pageSizes, setPageSizes] = useState<Record<number, PageSize>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function pickFile() {
    const [path] = await pickInputFiles(false);
    if (!path) return;

    setInputPath(path);
    setThumbnails([]);
    setError(null);
    setLoading(true);
    try {
      const { thumbnails: rendered, pageCount: count, pageSizes: sizes } = await renderPageThumbnails(
        path,
        maxWidthPx ? { maxWidthPx } : undefined,
      );
      setThumbnails(rendered);
      setPageCount(count);
      setPageSizes(sizes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load PDF.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setInputPath(null);
    setThumbnails([]);
    setPageCount(0);
    setPageSizes({});
    setError(null);
  }

  return { inputPath, pageCount, thumbnails, pageSizes, loading, error, pickFile, reset };
}
