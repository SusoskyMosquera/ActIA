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
      <h2>Subir grabación de audio</h2>

      <div className="form-group">
        <label htmlFor="audio-file">Archivo de audio</label>
        <div className={`file-input${isBusy ? ' is-disabled' : ''}`}>
          <label htmlFor="audio-file" className="file-button">Elegir archivo</label>
          <span className="file-name">
            {file ? file.name : 'Ningún archivo seleccionado'}
          </span>
          <input
            id="audio-file"
            className="visually-hidden"
            type="file"
            accept="audio/*"
            disabled={isBusy}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="language">Idioma</label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isBusy}
          >
            <option value="es">Español</option>
            <option value="en">Inglés</option>
            <option value="auto">Detección automática</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="model-size">Tamaño del modelo</label>
          <select
            id="model-size"
            value={modelSize}
            onChange={(e) => setModelSize(e.target.value)}
            disabled={isBusy}
          >
            <option value="tiny">Tiny (más rápido)</option>
            <option value="base">Base</option>
            <option value="small">Small (recomendado)</option>
            <option value="medium">Medium</option>
            <option value="large">Large (mejor precisión)</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="num-speakers">Número de oradores (opcional)</label>
        <input
          id="num-speakers"
          type="number"
          min="1"
          max="20"
          placeholder="Automático"
          value={numSpeakers}
          onChange={(e) => setNumSpeakers(e.target.value)}
          disabled={isBusy}
        />
      </div>

      <button
        type="submit"
        className="submit-btn"
        disabled={isBusy || !file}
      >
        {isBusy ? 'Procesando...' : 'Generar acta'}
      </button>
    </form>
  )
}
