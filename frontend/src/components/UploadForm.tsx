import { useState } from 'react'
import type { FormEvent } from 'react'
import type { TranscriptionOptions } from '../features/transcription/types'

interface UploadFormProps {
  onSubmit: (file: File, opts: TranscriptionOptions) => void
  isBusy: boolean
}

export default function UploadForm({ onSubmit, isBusy }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [language, setLanguage] = useState('es')
  const [modelSize, setModelSize] = useState('small')
  const [numSpeakers, setNumSpeakers] = useState('')

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!file) return

    const opts: TranscriptionOptions = {
      language,
      modelSize,
      ...(numSpeakers !== '' && { numSpeakers: Number(numSpeakers) }),
    }

    onSubmit(file, opts)
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h2>Upload Audio Recording</h2>

      <div className="form-group">
        <label htmlFor="audio-file">Audio File</label>
        <input
          id="audio-file"
          type="file"
          accept="audio/*"
          disabled={isBusy}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="language">Language</label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isBusy}
          >
            <option value="es">Spanish</option>
            <option value="en">English</option>
            <option value="auto">Auto-detect</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="model-size">Model Size</label>
          <select
            id="model-size"
            value={modelSize}
            onChange={(e) => setModelSize(e.target.value)}
            disabled={isBusy}
          >
            <option value="tiny">Tiny (fastest)</option>
            <option value="base">Base</option>
            <option value="small">Small (recommended)</option>
            <option value="medium">Medium</option>
            <option value="large">Large (best accuracy)</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="num-speakers">Number of Speakers (optional)</label>
        <input
          id="num-speakers"
          type="number"
          min="1"
          max="20"
          placeholder="Auto-detect"
          value={numSpeakers}
          onChange={(e) => setNumSpeakers(e.target.value)}
          disabled={isBusy}
          style={{ width: '100%', padding: '0.5rem 0.75rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.875rem' }}
        />
      </div>

      <button
        type="submit"
        className="submit-btn"
        disabled={isBusy || !file}
      >
        {isBusy ? 'Processing...' : 'Generate Minutes'}
      </button>
    </form>
  )
}
