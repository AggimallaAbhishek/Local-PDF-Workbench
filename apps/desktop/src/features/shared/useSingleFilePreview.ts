import { useState } from "react";
import { pickInputFiles } from "../../services/files";
import { renderPageThumbnails, type PageThumbnail } from "../../services/preview";

// Shared by split/rotate/organize: each operates on exactly one input PDF
// and needs its page thumbnails for a selection or reorder UI.
export function useSingleFilePreview() {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [thumbnails, setThumbnails] = useState<PageThumbnail[]>([]);
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
      const { thumbnails: rendered, pageCount: count } = await renderPageThumbnails(path);
      setThumbnails(rendered);
      setPageCount(count);
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
    setError(null);
  }

  return { inputPath, pageCount, thumbnails, loading, error, pickFile, reset };
}
