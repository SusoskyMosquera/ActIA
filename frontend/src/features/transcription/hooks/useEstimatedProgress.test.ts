import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useEstimatedProgress } from './useEstimatedProgress'

describe('useEstimatedProgress', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns null progress and null remainingMs when inactive', () => {
    const { result } = renderHook(() =>
      useEstimatedProgress(Date.now(), 10000, false, null, 'idle'),
    )
    expect(result.current.progress).toBeNull()
    expect(result.current.remainingMs).toBeNull()
    expect(result.current.elapsedMs).toBe(0)
  })

  it('returns null progress when startedAt is null', () => {
    const { result } = renderHook(() =>
      useEstimatedProgress(null, 10000, true, null, 'processing'),
    )
    expect(result.current.progress).toBeNull()
    expect(result.current.remainingMs).toBeNull()
  })

  it('computes correct progress and remainingMs for ANALYZING stage', async () => {
    const startedAt = Date.now()

    const { result } = renderHook(() =>
      useEstimatedProgress(startedAt, 10000, true, 'ANALYZING', 'processing'),
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(4000)
    })

    // ANALYZING duration: 10000 * 0.8 = 8000ms.
    // Elapsed: 4000ms. Progress fraction: 0.5.
    // ANALYZING range: [0.15, 0.75].
    // Progress: 0.15 + 0.5 * (0.75 - 0.15) = 0.45.
    expect(result.current.progress).toBeCloseTo(0.45, 2)
    expect(result.current.remainingMs).toBe(6000)
  })

  it('caps progress within the stage range even when elapsed exceeds stage duration', async () => {
    const startedAt = Date.now()

    const { result } = renderHook(() =>
      useEstimatedProgress(startedAt, 10000, true, 'GENERATING_MINUTES', 'processing'),
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(20000)
    })

    // GENERATING_MINUTES range: [0.75, 0.95].
    // Cap progress fraction at 0.99, so max progress = 0.75 + 0.99 * 0.20 = 0.948.
    expect(result.current.progress).toBeCloseTo(0.948, 2)
  })

  it('advances progress based on default durations when estimatedTotalMs is null', async () => {
    const startedAt = Date.now()

    const { result } = renderHook(() =>
      useEstimatedProgress(startedAt, null, true, 'ANALYZING', 'processing'),
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(15000)
    })

    // Default ANALYZING duration: 30000ms.
    // Elapsed: 15000ms. Progress fraction: 0.5.
    // ANALYZING range: [0.15, 0.75].
    // Progress: 0.15 + 0.5 * 0.60 = 0.45.
    expect(result.current.progress).toBeCloseTo(0.45, 2)
    expect(result.current.remainingMs).toBeNull()
  })

  it('resets stage started time when stage changes to smoothly transition ranges', async () => {
    const startedAt = Date.now()
    let stage: any = 'ANALYZING'

    const { result, rerender } = renderHook(() =>
      useEstimatedProgress(startedAt, 10000, true, stage, 'processing'),
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(4000)
    })

    expect(result.current.progress).toBeCloseTo(0.45, 2)

    // Now change stage to GENERATING_MINUTES
    stage = 'GENERATING_MINUTES'
    rerender()

    // Immediately after change, elapsed in new stage is 0, so progress is start of range = 0.75
    expect(result.current.progress).toBeCloseTo(0.75, 2)

    // Advance by 1000ms.
    // GENERATING_MINUTES duration: 10000 * 0.2 = 2000ms.
    // Fraction: 1000 / 2000 = 0.5.
    // Range: [0.75, 0.95]. Progress: 0.75 + 0.5 * 0.20 = 0.85.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000)
    })

    expect(result.current.progress).toBeCloseTo(0.85, 2)
  })
})
