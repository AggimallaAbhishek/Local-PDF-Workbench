export function PrivacyBadge() {
  return (
    <div className="flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
      <span className="h-2 w-2 rounded-full bg-emerald-500" />
      Processing is local — no cloud, no upload
    </div>
  );
}
