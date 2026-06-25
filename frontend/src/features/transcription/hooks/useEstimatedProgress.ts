import { useEffect, useState } from 'react'
import type { AppState, ProcessingStage } from '../types'

export interface EstimatedProgress {
  progress: number | null // 0..0.95, or null when indeterminate
  elapsedMs: number
  remainingMs: number | null
}

const STAGE_RANGES: Record<string, [number, number]> = {
  submitting: [0.0, 0.15],
  ANALYZING: [0.15, 0.75],
  TRANSCRIBING: [0.15, 0.50],
  DIARIZING: [0.50, 0.75],
  GENERATING_MINUTES: [0.75, 0.95],
}

const DEFAULT_STAGE_DURATIONS: Record<string, number> = {
  submitting: 5000,
  ANALYZING: 30000,
  TRANSCRIBING: 20000,
  DIARIZING: 10000,
  GENERATING_MINUTES: 10000,
}

export function useEstimatedProgress(
  startedAt: number | null,
  estimatedTotalMs: number | null,
  active: boolean,
  stage: ProcessingStage,
  status: AppState,
): EstimatedProgress {
  const [now, setNow] = useState(() => Date.now())
  const [currentStage, setCurrentStage] = useState<string | null>(null)
  const [stageStartedAt, setStageStartedAt] = useState<number | null>(null)

  useEffect(() => {
    if (!active || startedAt === null) {
      setCurrentStage(null)
      setStageStartedAt(null)
      return
    }

    const resolvedStage = status === 'submitting' ? 'submitting' : (stage || 'ANALYZING')
    if (resolvedStage !== currentStage) {
      setCurrentStage(resolvedStage)
      setStageStartedAt(Date.now())
    }
  }, [stage, status, active, currentStage, startedAt])

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

  const stageName = currentStage || (status === 'submitting' ? 'submitting' : (stage || 'ANALYZING'))
  const range = STAGE_RANGES[stageName] || [0.0, 0.95]
  const [startPct, endPct] = range

  let stageDuration = DEFAULT_STAGE_DURATIONS[stageName] || 10000
  if (estimatedTotalMs !== null && estimatedTotalMs > 0) {
    if (stageName === 'ANALYZING') {
      stageDuration = estimatedTotalMs * 0.8
    } else if (stageName === 'TRANSCRIBING') {
      stageDuration = estimatedTotalMs * 0.5
    } else if (stageName === 'DIARIZING') {
      stageDuration = estimatedTotalMs * 0.3
    } else if (stageName === 'GENERATING_MINUTES') {
      stageDuration = estimatedTotalMs * 0.2
    }
  }

  const currentStageStartedAt = stageStartedAt || startedAt
  const stageElapsedMs = Math.max(0, now - currentStageStartedAt)
  const stageProgressFraction = Math.min(0.99, stageElapsedMs / stageDuration)

  const progress = startPct + stageProgressFraction * (endPct - startPct)

  let remainingMs: number | null = null
  if (estimatedTotalMs !== null && estimatedTotalMs > 0) {
    remainingMs = Math.max(0, estimatedTotalMs - elapsedMs)
  }

  return { progress, elapsedMs, remainingMs }
}
