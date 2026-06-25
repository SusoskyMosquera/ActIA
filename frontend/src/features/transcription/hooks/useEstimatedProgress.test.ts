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
      useEstimatedProgress(Date.now(), 10000, false),
    )
    expect(result.current.progress).toBeNull()
    expect(result.current.remainingMs).toBeNull()
    expect(result.current.elapsedMs).toBe(0)
  })

  it('returns null progress when startedAt is null', () => {
    const { result } = renderHook(() =>
      useEstimatedProgress(null, 10000, true),
    )
    expect(result.current.progress).toBeNull()
    expect(result.current.remainingMs).toBeNull()
  })

  it('computes ~0.5 progress and ~5000 remainingMs after advancing 5000ms', async () => {
    const startedAt = Date.now()

    const { result } = renderHook(() =>
      useEstimatedProgress(startedAt, 10000, true),
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })

    expect(result.current.progress).toBeGreaterThanOrEqual(0.45)
    expect(result.current.progress).toBeLessThanOrEqual(0.55)
    expect(result.current.remainingMs).toBeGreaterThanOrEqual(4500)
    expect(result.current.remainingMs).toBeLessThanOrEqual(5500)
  })

  it('caps progress at 0.95 even when elapsed exceeds estimatedTotalMs', async () => {
    const startedAt = Date.now()

    const { result } = renderHook(() =>
      useEstimatedProgress(startedAt, 10000, true),
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(20000)
    })

    expect(result.current.progress).toBe(0.95)
  })

  it('returns null progress but increasing elapsedMs when estimatedTotalMs is null', async () => {
    const startedAt = Date.now()

    const { result } = renderHook(() =>
      useEstimatedProgress(startedAt, null, true),
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    expect(result.current.progress).toBeNull()
    expect(result.current.elapsedMs).toBeGreaterThan(0)
    expect(result.current.remainingMs).toBeNull()
  })
})
