import { useCallback, useEffect, useRef, useState } from 'react'
import { cancelTranscription, createTranscription, getTranscription } from '../api/transcriptionClient'
import { getAudioDurationMs } from '../../../lib/audioDuration'
import { unlockAudio, playDone, playError } from '../../../lib/notificationSound'
import type {
  AppState,
  JobResult,
  JobStatusResponse,
  ProcessingStage,
} from '../types'

// Rough CPU heuristic: diarization runs ~3x realtime + model load overhead
const CPU_FACTOR = 0.8
const BASE_OVERHEAD_MS = 10000

const POLL_INTERVAL_MS = 2000
// On CPU, real transcription + diarization can take tens of minutes. The backend
// stays the source of truth; this cap only guards against unbounded polling.
// Override with VITE_MAX_POLL_MINUTES.
const _envMaxMinutes = Number(import.meta.env.VITE_MAX_POLL_MINUTES)
const MAX_POLL_DURATION_MS =
  (Number.isFinite(_envMaxMinutes) && _envMaxMinutes > 0 ? _envMaxMinutes : 45) *
  60 *
  1000

interface UseTranscriptionJobReturn {
  state: AppState
  jobId: string | null
  stage: ProcessingStage
  result: JobResult | null
  error: string | null
  startedAt: number | null
  estimatedTotalMs: number | null
  submit: (file: File) => Promise<void>
  reset: () => void
  cancel: () => Promise<void>
}

export function useTranscriptionJob(): UseTranscriptionJobReturn {
  const [state, setState] = useState<AppState>('idle')
  const [jobId, setJobId] = useState<string | null>(null)
  const [stage, setStage] = useState<ProcessingStage>(null)
  const [result, setResult] = useState<JobResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [startedAt, setStartedAt] = useState<number | null>(null)
  const [estimatedTotalMs, setEstimatedTotalMs] = useState<number | null>(null)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollStartRef = useRef<number>(0)

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const handleJobUpdate = useCallback(
    (response: JobStatusResponse) => {
      setStage(response.stage)

      if (response.status === 'DONE') {
        stopPolling()
        setResult(response.result)
        setState('done')
        playDone()
      } else if (response.status === 'ERROR') {
        stopPolling()
        setError(response.error ?? 'Unknown error')
        setState('error')
        playError()
      } else if (response.status === 'CANCELLED') {
        // Server confirmed cancellation — return to idle so the user can start a new job.
        stopPolling()
        setStage(null)
        setState('idle')
        setJobId(null)
        setResult(null)
        setError(null)
      } else if (Date.now() - pollStartRef.current > MAX_POLL_DURATION_MS) {
        stopPolling()
        setError('Job timed out. Please try again.')
        setState('error')
      }
    },
    [stopPolling],
  )

  const startPolling = useCallback(
    (id: string) => {
      pollStartRef.current = Date.now()

      intervalRef.current = setInterval(() => {
        getTranscription(id)
          .then(handleJobUpdate)
          .catch((err: unknown) => {
            stopPolling()
            setError(err instanceof Error ? err.message : 'Polling failed')
            setState('error')
          })
      }, POLL_INTERVAL_MS)
    },
    [handleJobUpdate, stopPolling],
  )

  const submit = useCallback(
    async (file: File) => {
      // Runs from a user gesture — unlock audio for autoplay policy
      unlockAudio()
      setStartedAt(Date.now())
      setEstimatedTotalMs(null)
      // Kick off duration read in parallel; update estimate when ready
      void getAudioDurationMs(file).then((ms) => {
        if (ms !== null) setEstimatedTotalMs(ms * CPU_FACTOR + BASE_OVERHEAD_MS)
      })

      setState('submitting')
      setError(null)
      setResult(null)
      setJobId(null)
      setStage(null)

      try {
        const { jobId: newJobId } = await createTranscription(file)
        setJobId(newJobId)
        setState('processing')
        startPolling(newJobId)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Submission failed')
        setState('error')
      }
    },
    [startPolling],
  )

  const reset = useCallback(() => {
    stopPolling()
    setState('idle')
    setJobId(null)
    setStage(null)
    setResult(null)
    setError(null)
    setStartedAt(null)
    setEstimatedTotalMs(null)
  }, [stopPolling])

  const cancel = useCallback(async () => {
    // Capture the job id before reset clears it.
    const id = jobId
    // Optimistic: return to idle immediately so the user can start a new job.
    stopPolling()
    setState('idle')
    setJobId(null)
    setStage(null)
    setResult(null)
    setError(null)
    setStartedAt(null)
    setEstimatedTotalMs(null)
    // Best-effort server-side cancellation — ignore errors (job may have already finished).
    if (id) {
      try {
        await cancelTranscription(id)
      } catch {
        // intentionally swallowed — the optimistic reset already happened
      }
    }
  }, [jobId, stopPolling])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  return { state, jobId, stage, result, error, startedAt, estimatedTotalMs, submit, reset, cancel }
}
