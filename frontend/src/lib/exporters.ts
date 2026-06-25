import type { JobResult } from '../features/transcription/types'
import { buildMarkdownDocument, exportFilename } from './markdown'

/** Trigger a browser download for a blob. Thin DOM glue. */
function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

/** Download the full result as a Markdown file. */
export function downloadMarkdown(result: JobResult): void {
  const blob = new Blob([buildMarkdownDocument(result)], { type: 'text/markdown;charset=utf-8' })
  saveBlob(blob, exportFilename('md'))
}

/**
 * Download the full result as a Word (.docx) file. The heavy `docx` dependency
 * is loaded on demand here, so it stays out of the main bundle.
 */
export async function downloadDocx(result: JobResult): Promise<void> {
  const { buildDocxBlob } = await import('./docxExporter')
  saveBlob(await buildDocxBlob(result), exportFilename('docx'))
}

/** Copy the full Markdown export to the clipboard. */
export async function copyToClipboard(result: JobResult): Promise<void> {
  await navigator.clipboard.writeText(buildMarkdownDocument(result))
}
