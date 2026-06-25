import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createTranscription, getTranscription, ApiError } from './transcriptionClient'

describe('transcriptionClient', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_BASE_URL', '/api/v1')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  describe('createTranscription', () => {
    it('POSTs to /api/v1/transcriptions/ with trailing slash', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ job_id: 'abc123', status: 'PENDING' }), {
          status: 202,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      await createTranscription(file)

      expect(fetchSpy).toHaveBeenCalledOnce()
      const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit]
      expect(url).toBe('/api/v1/transcriptions/')
      expect(init.method).toBe('POST')
    })

    it('includes the file in FormData', async () => {
      let capturedBody: unknown = null

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(
        async (_url: string | URL | Request, init?: RequestInit) => {
          capturedBody = init?.body
          return new Response(JSON.stringify({ job_id: 'abc123', status: 'PENDING' }), {
            status: 202,
            headers: { 'Content-Type': 'application/json' },
          })
        },
      )

      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      await createTranscription(file)

      expect(capturedBody).not.toBeNull()
      expect((capturedBody as FormData).get('file')).toBe(file)
    })

    it('maps job_id to jobId in the response', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ job_id: 'xyz789', status: 'PENDING' }), {
          status: 202,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      const result = await createTranscription(file)

      expect(result.jobId).toBe('xyz789')
      expect(result.status).toBe('PENDING')
    })

    it('throws ApiError with correct status on non-2xx response', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Invalid file type' }), {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })
      await expect(createTranscription(file)).rejects.toThrow(ApiError)

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Invalid file type' }), {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      await expect(createTranscription(file)).rejects.toMatchObject({
        status: 422,
        message: 'Invalid file type',
      })
    })
  })

  describe('cancelTranscription', () => {
    it('POSTs to /transcriptions/{id}/cancel', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ job_id: 'abc123', status: 'PENDING' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      const { cancelTranscription } = await import('./transcriptionClient')
      await cancelTranscription('abc123')

      expect(fetchSpy).toHaveBeenCalledOnce()
      const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit]
      expect(url).toBe('/api/v1/transcriptions/abc123/cancel')
      expect(init.method).toBe('POST')
    })

    it('throws ApiError on non-2xx response', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Job is not cancellable (already finished)' }), {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      const { cancelTranscription, ApiError } = await import('./transcriptionClient')
      await expect(cancelTranscription('abc123')).rejects.toThrow(ApiError)
    })
  })

  describe('getTranscription', () => {
    it('GETs the correct URL for a job ID', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            job_id: 'abc123',
            status: 'PROCESSING',
            stage: 'ANALYZING',
            result: null,
            error: null,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )

      await getTranscription('abc123')

      expect(fetchSpy).toHaveBeenCalledWith('/api/v1/transcriptions/abc123')
    })

    it('returns full job status response', async () => {
      const mockResponse = {
        job_id: 'abc123',
        status: 'DONE' as const,
        stage: null,
        result: {
          transcript: [{ speaker: 'SPEAKER_00', start: 0, end: 5, text: 'Hello' }],
          minutes: '# Minutes',
          metadata: { duration_sec: 5, language: 'es', num_speakers: 1, model: 'assemblyai' },
        },
        error: null,
      }

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify(mockResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      const result = await getTranscription('abc123')
      expect(result.status).toBe('DONE')
      expect(result.result?.transcript).toHaveLength(1)
    })

    it('throws ApiError on 404', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Not found' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }),
      )

      await expect(getTranscription('nonexistent')).rejects.toThrow(ApiError)
    })
  })
})
