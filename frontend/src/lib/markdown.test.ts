import { describe, it, expect } from 'vitest'
import {
  parseInline,
  parseMarkdownBlocks,
  buildMarkdownDocument,
  exportFilename,
} from './markdown'
import type { JobResult } from '../features/transcription/types'

describe('parseInline', () => {
  it('returns a single non-bold run for plain text', () => {
    expect(parseInline('plain text')).toEqual([{ text: 'plain text', bold: false }])
  })

  it('splits **bold** segments into bold runs', () => {
    expect(parseInline('a **b** c')).toEqual([
      { text: 'a ', bold: false },
      { text: 'b', bold: true },
      { text: ' c', bold: false },
    ])
  })

  it('handles text that is entirely bold', () => {
    expect(parseInline('**all**')).toEqual([{ text: 'all', bold: true }])
  })

  it('handles multiple bold segments', () => {
    expect(parseInline('**x** y **z**')).toEqual([
      { text: 'x', bold: true },
      { text: ' y ', bold: false },
      { text: 'z', bold: true },
    ])
  })
})

describe('parseMarkdownBlocks', () => {
  it('parses headings with their level (capped at 3)', () => {
    expect(parseMarkdownBlocks('# Title')).toEqual([{ type: 'heading', level: 1, text: 'Title' }])
    expect(parseMarkdownBlocks('## Sub')).toEqual([{ type: 'heading', level: 2, text: 'Sub' }])
    expect(parseMarkdownBlocks('### Deep')).toEqual([{ type: 'heading', level: 3, text: 'Deep' }])
    expect(parseMarkdownBlocks('#### Deeper')).toEqual([
      { type: 'heading', level: 3, text: 'Deeper' },
    ])
  })

  it('parses - and * as bullets', () => {
    expect(parseMarkdownBlocks('- one\n* two')).toEqual([
      { type: 'bullet', text: 'one' },
      { type: 'bullet', text: 'two' },
    ])
  })

  it('keeps numbered list items as paragraphs (lossless)', () => {
    expect(parseMarkdownBlocks('1. first')).toEqual([{ type: 'paragraph', text: '1. first' }])
  })

  it('treats other lines as paragraphs and skips blank lines', () => {
    expect(parseMarkdownBlocks('hello\n\nworld')).toEqual([
      { type: 'paragraph', text: 'hello' },
      { type: 'paragraph', text: 'world' },
    ])
  })
})

const sampleResult: JobResult = {
  transcript: [
    { speaker: 'SPEAKER_00', start: 0, end: 5, text: 'Hola a todos.' },
    { speaker: 'SPEAKER_01', start: 5, end: 12, text: 'Buenos días.' },
  ],
  minutes: '# Acta\n\n## Temas\n\n- Punto uno',
  metadata: { duration_sec: 65, language: 'es', num_speakers: 2, model: 'speechmatics' },
}

describe('buildMarkdownDocument', () => {
  it('includes a metadata details section', () => {
    const doc = buildMarkdownDocument(sampleResult)
    expect(doc).toContain('## Detalles')
    expect(doc).toContain('**Duración:** 1m 5s')
    expect(doc).toContain('**Idioma:** ES')
    expect(doc).toContain('**Oradores:** 2')
    expect(doc).toContain('**Modelo:** speechmatics')
  })

  it('embeds the generated minutes verbatim', () => {
    const doc = buildMarkdownDocument(sampleResult)
    expect(doc).toContain('# Acta')
    expect(doc).toContain('- Punto uno')
  })

  it('renders the transcript with speaker, timestamps and text', () => {
    const doc = buildMarkdownDocument(sampleResult)
    expect(doc).toContain('## Transcripción')
    expect(doc).toContain('**SPEAKER_00** · 00:00 — 00:05')
    expect(doc).toContain('Hola a todos.')
    expect(doc).toContain('**SPEAKER_01** · 00:05 — 00:12')
  })
})

describe('exportFilename', () => {
  it('builds an actia-acta-YYYY-MM-DD.<ext> name', () => {
    const date = new Date(2026, 5, 24) // local June 24, 2026
    expect(exportFilename('md', date)).toBe('actia-acta-2026-06-24.md')
    expect(exportFilename('docx', date)).toBe('actia-acta-2026-06-24.docx')
  })
})
