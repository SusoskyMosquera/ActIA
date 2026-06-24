import { useCallback, useEffect, useRef, useState } from 'react'
import { createTranscription, getTranscription } from '../api/transcriptionClient'
import type {
  AppState,
  JobResult,
  JobStatusResponse,
  ProcessingStage,
  TranscriptionOptions,
} from '../types'

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
  submit: (file: File, opts: TranscriptionOptions) => Promise<void>
  reset: () => void
}

export function useTranscriptionJob(): UseTranscriptionJobReturn {
  const [state, setState] = useState<AppState>('idle')
  const [jobId, setJobId] = useState<string | null>(null)
  const [stage, setStage] = useState<ProcessingStage>(null)
  const [result, setResult] = useState<JobResult | null>(null)
  const [error, setError] = useState<string | null>(null)

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
      } else if (response.status === 'ERROR') {
        stopPolling()
        setError(response.error ?? 'Unknown error')
        setState('error')
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
    async (file: File, opts: TranscriptionOptions) => {
      setState('submitting')
      setError(null)
      setResult(null)
      setJobId(null)
      setStage(null)

      try {
        const { jobId: newJobId } = await createTranscription(file, opts)
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
  }, [stopPolling])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  return { state, jobId, stage, result, error, submit, reset }
}
