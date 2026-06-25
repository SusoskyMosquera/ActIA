import type {
  CreateTranscriptionResponse,
  JobStatusResponse,
  TranscriptionOptions,
} from '../types'

const DEFAULT_BASE_URL = '/api/v1'

function getBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function assertOk(response: Response): Promise<void> {
  if (!response.ok) {
    let message = `HTTP ${response.status}: ${response.statusText}`
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // ignore parse error, keep default message
    }
    throw new ApiError(response.status, message)
  }
}

export async function createTranscription(
  file: File,
  opts: TranscriptionOptions,
): Promise<CreateTranscriptionResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('language', opts.language)
  if (opts.numSpeakers !== undefined) {
    formData.append('num_speakers', String(opts.numSpeakers))
  }

  const response = await fetch(`${getBaseUrl()}/transcriptions/`, {
    method: 'POST',
    body: formData,
  })

  await assertOk(response)

  const data = await response.json() as { job_id: string; status: string }
  return {
    jobId: data.job_id,
    status: data.status as CreateTranscriptionResponse['status'],
  }
}

export async function getTranscription(
  jobId: string,
): Promise<JobStatusResponse> {
  const response = await fetch(`${getBaseUrl()}/transcriptions/${jobId}`)
  await assertOk(response)
  return response.json() as Promise<JobStatusResponse>
}

export async function cancelTranscription(jobId: string): Promise<void> {
  const response = await fetch(`${getBaseUrl()}/transcriptions/${jobId}/cancel`, {
    method: 'POST',
  })
  await assertOk(response)
}
