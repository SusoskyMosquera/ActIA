import { useState } from 'react'
import type { JobResult } from '../features/transcription/types'
import { copyToClipboard, downloadDocx, downloadMarkdown } from '../lib/exporters'

interface ExportMenuProps {
  result: JobResult
}

export default function ExportMenu({ result }: ExportMenuProps) {
  const [copied, setCopied] = useState(false)
  const [busyDocx, setBusyDocx] = useState(false)

  async function handleCopy() {
    try {
      await copyToClipboard(result)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // The Clipboard API is unavailable outside secure contexts; fail quietly.
    }
  }

  async function handleDocx() {
    setBusyDocx(true)
    try {
      await downloadDocx(result)
    } finally {
      setBusyDocx(false)
    }
  }

  return (
    <div className="export-menu">
      <span className="export-label">Exportar</span>
      <button type="button" className="export-button" onClick={() => downloadMarkdown(result)}>
        Markdown
      </button>
      <button
        type="button"
        className="export-button"
        onClick={handleDocx}
        disabled={busyDocx}
      >
        {busyDocx ? 'Generando…' : 'Word (.docx)'}
      </button>
      <button type="button" className="export-button" onClick={handleCopy}>
        {copied ? '¡Copiado!' : 'Copiar'}
      </button>
    </div>
  )
}
