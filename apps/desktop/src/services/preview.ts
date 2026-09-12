import { convertFileSrc } from "@tauri-apps/api/core";
import { appCacheDir, join } from "@tauri-apps/api/path";
import { runJob } from "./engine";

export interface PageThumbnail {
  page: number;
  src: string; // asset:// URL, safe to use as an <img> src
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
  pages?: number[],
): Promise<{ thumbnails: PageThumbnail[]; pageCount: number }> {
  const outputDir = await previewCacheDir();
  const result = await runJob({
    jobId: crypto.randomUUID(),
    tool: "preview",
    inputs: [inputPath],
    options: pages ? { pages } : {},
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

  return {
    thumbnails,
    pageCount: (result.metadata?.pageCount as number | undefined) ?? thumbnails.length,
  };
}
