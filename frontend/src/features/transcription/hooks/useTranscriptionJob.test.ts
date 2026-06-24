import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTranscriptionJob } from './useTranscriptionJob'
import * as client from '../api/transcriptionClient'

vi.mock('../api/transcriptionClient')

const mockCreateTranscription = vi.mocked(client.createTranscription)
const mockGetTranscription = vi.mocked(client.getTranscription)

describe('useTranscriptionJob', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.resetAllMocks()
  })

  it('starts in idle state', () => {
    const { result } = renderHook(() => useTranscriptionJob())
    expect(result.current.state).toBe('idle')
    expect(result.current.jobId).toBeNull()
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('transitions to submitting then processing after submit', async () => {
    mockCreateTranscription.mockResolvedValueOnce({ jobId: 'job-1', status: 'PENDING' })
    mockGetTranscription.mockResolvedValue({
      job_id: 'job-1',
      status: 'PROCESSING',
      stage: 'TRANSCRIBING',
      result: null,
      error: null,
    })

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      void result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    // After submission completes
    await act(async () => {
      await vi.runAllTicks()
    })

    expect(result.current.state).toBe('processing')
    expect(result.current.jobId).toBe('job-1')
  })

  it('updates stage while polling', async () => {
    mockCreateTranscription.mockResolvedValueOnce({ jobId: 'job-2', status: 'PENDING' })
    mockGetTranscription
      .mockResolvedValueOnce({
        job_id: 'job-2',
        status: 'PROCESSING',
        stage: 'TRANSCRIBING',
        result: null,
        error: null,
      })
      .mockResolvedValueOnce({
        job_id: 'job-2',
        status: 'PROCESSING',
        stage: 'DIARIZING',
        result: null,
        error: null,
      })
      .mockResolvedValueOnce({
        job_id: 'job-2',
        status: 'PROCESSING',
        stage: 'GENERATING_MINUTES',
        result: null,
        error: null,
      })

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      void result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    await act(async () => {
      await vi.runAllTicks()
    })

    // First poll
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.stage).toBe('TRANSCRIBING')

    // Second poll
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.stage).toBe('DIARIZING')

    // Third poll
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.stage).toBe('GENERATING_MINUTES')
  })

  it('transitions to done when status is DONE and exposes result', async () => {
    const mockResult = {
      transcript: [{ speaker: 'SPEAKER_00', start: 0, end: 5, text: 'Hello' }],
      minutes: '# Meeting Minutes',
      metadata: { duration_sec: 5, language: 'es', num_speakers: 1, model: 'small' },
    }

    mockCreateTranscription.mockResolvedValueOnce({ jobId: 'job-3', status: 'PENDING' })
    mockGetTranscription.mockResolvedValueOnce({
      job_id: 'job-3',
      status: 'DONE',
      stage: null,
      result: mockResult,
      error: null,
    })

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      void result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    await act(async () => {
      await vi.runAllTicks()
    })

    // Trigger one poll cycle
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.state).toBe('done')
    expect(result.current.result).toEqual(mockResult)
    expect(result.current.error).toBeNull()
  })

  it('stops polling after DONE', async () => {
    const mockResult = {
      transcript: [],
      minutes: '',
      metadata: { duration_sec: 0, language: 'es', num_speakers: 0, model: 'small' },
    }

    mockCreateTranscription.mockResolvedValueOnce({ jobId: 'job-4', status: 'PENDING' })
    mockGetTranscription.mockResolvedValue({
      job_id: 'job-4',
      status: 'DONE',
      stage: null,
      result: mockResult,
      error: null,
    })

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      void result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    await act(async () => {
      await vi.runAllTicks()
    })

    // First poll → DONE
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.state).toBe('done')
    const callCountAfterDone = mockGetTranscription.mock.calls.length

    // Advance more time — should NOT poll again
    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000)
    })

    expect(mockGetTranscription.mock.calls.length).toBe(callCountAfterDone)
  })

  it('transitions to error when status is ERROR and exposes error message', async () => {
    mockCreateTranscription.mockResolvedValueOnce({ jobId: 'job-5', status: 'PENDING' })
    mockGetTranscription.mockResolvedValueOnce({
      job_id: 'job-5',
      status: 'ERROR',
      stage: null,
      result: null,
      error: 'Transcription failed: GPU out of memory',
    })

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      void result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    await act(async () => {
      await vi.runAllTicks()
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.state).toBe('error')
    expect(result.current.error).toBe('Transcription failed: GPU out of memory')
    expect(result.current.result).toBeNull()
  })

  it('stops polling after ERROR', async () => {
    mockCreateTranscription.mockResolvedValueOnce({ jobId: 'job-6', status: 'PENDING' })
    mockGetTranscription.mockResolvedValue({
      job_id: 'job-6',
      status: 'ERROR',
      stage: null,
      result: null,
      error: 'Failed',
    })

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      void result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    await act(async () => {
      await vi.runAllTicks()
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.state).toBe('error')
    const callCountAfterError = mockGetTranscription.mock.calls.length

    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000)
    })

    expect(mockGetTranscription.mock.calls.length).toBe(callCountAfterError)
  })

  it('resets to idle state when reset() is called', async () => {
    mockCreateTranscription.mockResolvedValueOnce({ jobId: 'job-7', status: 'PENDING' })
    mockGetTranscription.mockResolvedValue({
      job_id: 'job-7',
      status: 'DONE',
      stage: null,
      result: {
        transcript: [],
        minutes: '',
        metadata: { duration_sec: 0, language: 'es', num_speakers: 0, model: 'small' },
      },
      error: null,
    })

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      void result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    await act(async () => {
      await vi.runAllTicks()
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000)
    })

    expect(result.current.state).toBe('done')

    act(() => {
      result.current.reset()
    })

    expect(result.current.state).toBe('idle')
    expect(result.current.jobId).toBeNull()
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('handles submit failure (network error) gracefully', async () => {
    mockCreateTranscription.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useTranscriptionJob())

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    await act(async () => {
      await result.current.submit(file, { language: 'es', modelSize: 'small' })
    })

    expect(result.current.state).toBe('error')
    expect(result.current.error).toBe('Network error')
  })
})
