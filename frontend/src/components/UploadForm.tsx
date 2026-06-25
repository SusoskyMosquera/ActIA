import { useRef, useState } from 'react'
import type { DragEvent, FormEvent } from 'react'

interface UploadFormProps {
  onSubmit: (file: File) => void
  isBusy: boolean
}

export default function UploadForm({ onSubmit, isBusy }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!file) return
    onSubmit(file)
  }

  const acceptDropped = (dropped: File | undefined) => {
    if (!dropped) return
    // Accept audio files; some browsers leave the type empty for certain files.
    if (dropped.type === '' || dropped.type.startsWith('audio/')) {
      setFile(dropped)
    }
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (!isBusy) setIsDragging(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    if (!isBusy) acceptDropped(e.dataTransfer.files?.[0])
  }

  const openPicker = () => {
    if (!isBusy) inputRef.current?.click()
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h2>Subir grabación de audio</h2>

      <div className="form-group">
        <label htmlFor="audio-file">Archivo de audio</label>
        <div
          className={`dropzone${isDragging ? ' is-dragover' : ''}${isBusy ? ' is-disabled' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={openPicker}
          role="button"
          tabIndex={isBusy ? -1 : 0}
          onKeyDown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !isBusy) {
              e.preventDefault()
              openPicker()
            }
          }}
        >
          <input
            ref={inputRef}
            id="audio-file"
            className="visually-hidden"
            type="file"
            accept="audio/*"
            disabled={isBusy}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <p className="dropzone-text">
            {file
              ? file.name
              : 'Arrastra un archivo de audio aquí o haz click para elegir un archivo'}
          </p>
        </div>
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
