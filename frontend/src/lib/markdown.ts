import type { JobResult } from '../features/transcription/types'
import { formatClock, formatDuration } from './format'

/** A run of inline text with a bold flag — the unit a docx TextRun maps to. */
export interface InlineRun {
  text: string
  bold: boolean
}

/** A block-level element parsed from markdown, kept renderer-agnostic. */
export type MarkdownBlock =
  | { type: 'heading'; level: 1 | 2 | 3; text: string }
  | { type: 'bullet'; text: string }
  | { type: 'paragraph'; text: string }

/**
 * Split a line into bold / non-bold runs on `**...**`.
 * Pure and renderer-agnostic so it can feed both docx and plain output.
 */
export function parseInline(text: string): InlineRun[] {
  const runs: InlineRun[] = []
  const pattern = /\*\*(.+?)\*\*/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      runs.push({ text: text.slice(lastIndex, match.index), bold: false })
    }
    runs.push({ text: match[1], bold: true })
    lastIndex = pattern.lastIndex
  }

  if (lastIndex < text.length) {
    runs.push({ text: text.slice(lastIndex), bold: false })
  }

  return runs.length > 0 ? runs : [{ text, bold: false }]
}

/**
 * Parse a markdown string into block elements. Handles the subset an LLM-
 * generated acta actually uses: ATX headings (capped at level 3), `-`/`*`
 * bullets, and paragraphs. Numbered items are kept verbatim as paragraphs
 * (lossless) and blank lines are dropped.
 */
export function parseMarkdownBlocks(markdown: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = []

  for (const rawLine of markdown.split('\n')) {
    const line = rawLine.trimEnd()
    if (line.trim() === '') continue

    const heading = /^(#{1,6})\s+(.*)$/.exec(line)
    if (heading) {
      const level = Math.min(heading[1].length, 3) as 1 | 2 | 3
      blocks.push({ type: 'heading', level, text: heading[2].trim() })
      continue
    }

    const bullet = /^[-*]\s+(.*)$/.exec(line)
    if (bullet) {
      blocks.push({ type: 'bullet', text: bullet[1].trim() })
      continue
    }

    blocks.push({ type: 'paragraph', text: line.trim() })
  }

  return blocks
}

/**
 * Build the full, self-contained markdown export: metadata, the generated
 * minutes verbatim, and the speaker-attributed transcript. Pure.
 */
export function buildMarkdownDocument(result: JobResult): string {
  const { transcript, minutes, metadata } = result

  const details = [
    '## Detalles',
    '',
    `- **Duración:** ${formatDuration(metadata.duration_sec)}`,
    `- **Idioma:** ${metadata.language.toUpperCase()}`,
    `- **Oradores:** ${metadata.num_speakers}`,
    `- **Modelo:** ${metadata.model}`,
  ].join('\n')

  const transcriptLines = transcript
    .map(
      (s) =>
        `**${s.speaker}** · ${formatClock(s.start)} — ${formatClock(s.end)}\n${s.text}`,
    )
    .join('\n\n')

  return [
    '# Acta de reunión',
    '',
    details,
    '',
    '---',
    '',
    minutes.trim(),
    '',
    '---',
    '',
    '## Transcripción',
    '',
    transcriptLines,
    '',
  ].join('\n')
}

/** `actia-acta-YYYY-MM-DD.<ext>` using the local date. */
export function exportFilename(ext: string, now: Date = new Date()): string {
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `actia-acta-${y}-${m}-${d}.${ext}`
}
