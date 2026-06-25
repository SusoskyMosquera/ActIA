import { describe, it, expect, vi, afterEach } from 'vitest'
import { copyToClipboard } from './exporters'
import { buildMarkdownDocument } from './markdown'
import type { JobResult } from '../features/transcription/types'

const sampleResult: JobResult = {
  transcript: [{ speaker: 'SPEAKER_00', start: 0, end: 5, text: 'Hola.' }],
  minutes: '# Acta\n\n## Temas\n\n- Punto uno',
  metadata: { duration_sec: 65, language: 'es', num_speakers: 2, model: 'speechmatics' },
}

describe('copyToClipboard', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('writes the full markdown export to the clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    await copyToClipboard(sampleResult)

    expect(writeText).toHaveBeenCalledOnce()
    expect(writeText).toHaveBeenCalledWith(buildMarkdownDocument(sampleResult))
  })
})
