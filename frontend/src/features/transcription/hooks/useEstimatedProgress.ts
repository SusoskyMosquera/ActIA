import { useEffect, useState } from 'react'

export interface EstimatedProgress {
  progress: number | null // 0..0.95, or null when indeterminate
  elapsedMs: number
  remainingMs: number | null
}

export function useEstimatedProgress(
  startedAt: number | null,
  estimatedTotalMs: number | null,
  active: boolean,
): EstimatedProgress {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (!active || startedAt === null) return
    setNow(Date.now())
    const id = setInterval(() => setNow(Date.now()), 500)
    return () => clearInterval(id)
  }, [active, startedAt])

  if (!active || startedAt === null) {
    return { progress: null, elapsedMs: 0, remainingMs: null }
  }
  const elapsedMs = Math.max(0, now - startedAt)
  if (estimatedTotalMs === null || estimatedTotalMs <= 0) {
    return { progress: null, elapsedMs, remainingMs: null }
  }
  const progress = Math.min(0.95, elapsedMs / estimatedTotalMs)
  const remainingMs = Math.max(0, estimatedTotalMs - elapsedMs)
  return { progress, elapsedMs, remainingMs }
}
