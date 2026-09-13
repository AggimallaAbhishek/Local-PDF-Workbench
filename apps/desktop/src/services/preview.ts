import { convertFileSrc } from "@tauri-apps/api/core";
import { appCacheDir, join } from "@tauri-apps/api/path";
import { runJob } from "./engine";

export interface PageThumbnail {
  page: number;
  src: string; // asset:// URL, safe to use as an <img> src
}

export interface PageSize {
  width: number; // in PDF points, matching the page's own mediabox
  height: number;
}

// Thumbnails are ephemeral UI aids, not user-requested job outputs, so they
// render into the app's own cache dir rather than the output dir the user
// picks for a job. `run_job`/the engine auto-create this directory.
async function previewCacheDir(): Promise<string> {
  const cache = await appCacheDir();
  return join(cache, "previews");
}

export async function renderPageThumbnails(
  inputPath: string,
  options?: { pages?: number[]; maxWidthPx?: number },
): Promise<{ thumbnails: PageThumbnail[]; pageCount: number; pageSizes: Record<number, PageSize> }> {
  const outputDir = await previewCacheDir();
  const result = await runJob({
    jobId: crypto.randomUUID(),
    tool: "preview",
    inputs: [inputPath],
    options: {
      ...(options?.pages ? { pages: options.pages } : {}),
      ...(options?.maxWidthPx ? { maxWidthPx: options.maxWidthPx } : {}),
    },
    outputDir,
  });

  if (result.status !== "success") {
    throw new Error(result.error?.message ?? "Failed to render page previews.");
  }

  const renderedPages = (result.metadata?.renderedPages as number[] | undefined) ?? [];
  const thumbnails = result.outputs.map((path, i) => ({
    page: renderedPages[i] ?? i + 1,
    src: convertFileSrc(path),
  }));

  const rawSizes = (result.metadata?.pageSizes as Record<string, [number, number]> | undefined) ?? {};
  const pageSizes: Record<number, PageSize> = {};
  for (const [key, [width, height]] of Object.entries(rawSizes)) {
    pageSizes[Number(key)] = { width, height };
  }

  return {
    thumbnails,
    pageCount: (result.metadata?.pageCount as number | undefined) ?? thumbnails.length,
    pageSizes,
  };
}
