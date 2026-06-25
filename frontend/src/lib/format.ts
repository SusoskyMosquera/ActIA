/** Pure time formatting helpers shared by the UI and the exporters. */

/** Seconds → zero-padded `mm:ss` (e.g. 65 → "01:05"). */
export function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

/** Seconds → human duration (e.g. 5 → "5s", 65 → "1m 5s"). */
export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}
