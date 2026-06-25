import { Document, HeadingLevel, Packer, Paragraph, TextRun } from 'docx'
import type { JobResult } from '../features/transcription/types'
import { formatClock, formatDuration } from './format'
import { parseInline, parseMarkdownBlocks, type MarkdownBlock } from './markdown'

/*
 * Lives in its own module so it can be loaded with a dynamic import(): the
 * heavy `docx` dependency is code-split into a lazy chunk and only fetched when
 * the user actually exports to Word, keeping the main bundle light.
 */

const HEADING_BY_LEVEL = {
  1: HeadingLevel.HEADING_1,
  2: HeadingLevel.HEADING_2,
  3: HeadingLevel.HEADING_3,
} as const

/** Map parsed markdown blocks to docx paragraphs (headings, bullets, text). */
export function blocksToDocxParagraphs(blocks: MarkdownBlock[]): Paragraph[] {
  return blocks.map((block) => {
    const children = parseInline(block.text).map(
      (run) => new TextRun({ text: run.text, bold: run.bold }),
    )

    if (block.type === 'heading') {
      return new Paragraph({ heading: HEADING_BY_LEVEL[block.level], children })
    }
    if (block.type === 'bullet') {
      return new Paragraph({ bullet: { level: 0 }, children })
    }
    return new Paragraph({ children })
  })
}

function labelledBullet(label: string, value: string): Paragraph {
  return new Paragraph({
    bullet: { level: 0 },
    children: [new TextRun({ text: `${label}: `, bold: true }), new TextRun(value)],
  })
}

/**
 * Build a clean Word document from the structured result: title, metadata,
 * the generated minutes (markdown → paragraphs), and the transcript.
 */
export function buildDocxDocument(result: JobResult): Document {
  const { transcript, minutes, metadata } = result

  const children: Paragraph[] = [
    new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun('Acta de reunión')] }),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('Detalles')] }),
    labelledBullet('Duración', formatDuration(metadata.duration_sec)),
    labelledBullet('Idioma', metadata.language.toUpperCase()),
    labelledBullet('Oradores', String(metadata.num_speakers)),
    labelledBullet('Modelo', metadata.model),
    ...blocksToDocxParagraphs(parseMarkdownBlocks(minutes)),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('Transcripción')] }),
  ]

  for (const s of transcript) {
    children.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `${s.speaker} · ${formatClock(s.start)} — ${formatClock(s.end)}`,
            bold: true,
          }),
        ],
      }),
    )
    children.push(new Paragraph({ children: [new TextRun(s.text)] }))
  }

  return new Document({ sections: [{ children }] })
}

/** Render the result to a .docx Blob. */
export function buildDocxBlob(result: JobResult): Promise<Blob> {
  return Packer.toBlob(buildDocxDocument(result))
}
