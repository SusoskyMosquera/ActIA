export type JobStatus = 'PENDING' | 'PROCESSING' | 'DONE' | 'ERROR' | 'CANCELLED'

export type ProcessingStage =
  | 'TRANSCRIBING'
  | 'DIARIZING'
  | 'GENERATING_MINUTES'
  | null

export interface TranscriptSegment {
  speaker: string
  start: number
  end: number
  text: string
}

export interface JobMetadata {
  duration_sec: number
  language: string
  num_speakers: number
  model: string
}

export interface JobResult {
  transcript: TranscriptSegment[]
  minutes: string
  metadata: JobMetadata
}

export interface JobStatusResponse {
  job_id: string
  status: JobStatus
  stage: ProcessingStage
  result: JobResult | null
  error: string | null
}

export interface CreateTranscriptionResponse {
  jobId: string
  status: JobStatus
}

export interface TranscriptionOptions {
  language: string
  modelSize: string
  numSpeakers?: number
}

export type AppState = 'idle' | 'submitting' | 'processing' | 'done' | 'error'
