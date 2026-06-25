import { describe, it, expect } from 'vitest'
import { Document, Paragraph } from 'docx'
import { blocksToDocxParagraphs, buildDocxDocument } from './docxExporter'
import { parseMarkdownBlocks } from './markdown'
import type { JobResult } from '../features/transcription/types'

const sampleResult: JobResult = {
  transcript: [{ speaker: 'SPEAKER_00', start: 0, end: 5, text: 'Hola.' }],
  minutes: '# Acta\n\n## Temas\n\n- Punto uno',
  metadata: { duration_sec: 65, language: 'es', num_speakers: 2, model: 'speechmatics' },
}

describe('blocksToDocxParagraphs', () => {
  it('produces one Paragraph per block', () => {
    const blocks = parseMarkdownBlocks('# Title\n- a\nplain')
    const paragraphs = blocksToDocxParagraphs(blocks)
    expect(paragraphs).toHaveLength(3)
    paragraphs.forEach((p) => expect(p).toBeInstanceOf(Paragraph))
  })
})

describe('buildDocxDocument', () => {
  it('returns a docx Document instance', () => {
    expect(buildDocxDocument(sampleResult)).toBeInstanceOf(Document)
  })
})
