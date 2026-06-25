import { useRef, useState, useEffect } from 'react'
import type { DragEvent, FormEvent } from 'react'

interface UploadFormProps {
  onSubmit: (file: File) => void
  isBusy: boolean
}

const MicIcon = () => (
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
    <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
    <line x1="12" x2="12" y1="19" y2="22" />
  </svg>
)

const StopIcon = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="4" y="4" width="16" height="16" rx="2" />
  </svg>
)

const PauseIcon = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <line x1="10" x2="10" y1="4" y2="20" />
    <line x1="14" x2="14" y1="4" y2="20" />
  </svg>
)

const PlayIcon = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polygon points="5 3 19 12 5 21 5 3" />
  </svg>
)

const TrashIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M3 6h18" />
    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
  </svg>
)

export default function UploadForm({ onSubmit, isBusy }: UploadFormProps) {
  const [mode, setMode] = useState<'upload' | 'record'>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Recording states
  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  const inputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

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

  const discardRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }
    setFile(null)
    setIsRecording(false)
    setIsPaused(false)
    setRecordingDuration(0)
  }

  const handleTabChange = (newMode: 'upload' | 'record') => {
    if (isBusy) return
    setMode(newMode)
    setFile(null)
    setError(null)
    discardRecording()
  }

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  const getSupportedMimeType = () => {
    if (typeof MediaRecorder === 'undefined') return ''
    const types = ['audio/webm', 'audio/mp4', 'audio/ogg', 'audio/wav']
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) return type
    }
    return ''
  }

  const getExtensionForMime = (mime: string) => {
    if (mime.includes('webm')) return 'webm'
    if (mime.includes('mp4') || mime.includes('m4a')) return 'm4a'
    if (mime.includes('ogg')) return 'ogg'
    if (mime.includes('wav')) return 'wav'
    return 'webm'
  }

  const formatTime = (secs: number) => {
    const mm = Math.floor(secs / 60)
      .toString()
      .padStart(2, '0')
    const ss = (secs % 60).toString().padStart(2, '0')
    return `${mm}:${ss}`
  }

  const startRecording = async () => {
    setError(null)
    setFile(null)
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }
    chunksRef.current = []

    try {
      if (typeof navigator === 'undefined' || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('La API de grabación de audio no está soportada o no está en un contexto seguro.')
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mimeType = getSupportedMimeType()
      const options = mimeType ? { mimeType } : undefined
      const mediaRecorder = new MediaRecorder(stream, options)
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = () => {
        const actualMime = mediaRecorder.mimeType || mimeType || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type: actualMime })
        const url = URL.createObjectURL(blob)
        setAudioUrl(url)

        const ext = getExtensionForMime(actualMime)
        const recordedFile = new File([blob], `grabacion-${Date.now()}.${ext}`, {
          type: actualMime,
        })
        setFile(recordedFile)
      }

      mediaRecorder.start(250)
      setIsRecording(true)
      setIsPaused(false)
      setRecordingDuration(0)

      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1)
      }, 1000)
    } catch (err) {
      setError(
        err instanceof Error
          ? `No se pudo acceder al micrófono: ${err.message}`
          : 'No se pudo acceder al micrófono',
      )
    }
  }

  const pauseRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause()
      setIsPaused(true)
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }

  const resumeRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume()
      setIsPaused(false)
      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1)
      }, 1000)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    setIsRecording(false)
    setIsPaused(false)
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div className="upload-tabs">
        <button
          type="button"
          className={`tab-btn${mode === 'upload' ? ' is-active' : ''}`}
          onClick={() => handleTabChange('upload')}
          disabled={isBusy}
        >
          Subir archivo
        </button>
        <button
          type="button"
          className={`tab-btn${mode === 'record' ? ' is-active' : ''}`}
          onClick={() => handleTabChange('record')}
          disabled={isBusy}
        >
          Grabar audio
        </button>
      </div>

      {mode === 'upload' ? (
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
      ) : (
        <div className="form-group">
          <label>Grabación en vivo</label>
          <div className="recording-panel">
            {error && (
              <div className="error-banner" style={{ margin: 0, width: '100%' }}>
                {error}
              </div>
            )}

            {!isRecording && !audioUrl && (
              <>
                <p className="dropzone-text">
                  Haz click en el botón para comenzar a grabar la reunión desde el navegador.
                </p>
                <button
                  type="button"
                  className="record-btn-main"
                  onClick={startRecording}
                  disabled={isBusy}
                  aria-label="Iniciar grabación"
                >
                  <MicIcon />
                </button>
              </>
            )}

            {isRecording && (
              <>
                <div className="recording-visualizer">
                  {[...Array(7)].map((_, i) => (
                    <div
                      key={i}
                      className={`visualizer-bar${isRecording && !isPaused ? ' is-active' : ''}`}
                    />
                  ))}
                </div>
                <div className="recording-timer">{formatTime(recordingDuration)}</div>
                <div className="recording-controls">
                  {isPaused ? (
                    <button
                      type="button"
                      className="record-action-btn"
                      onClick={resumeRecording}
                      title="Reanudar"
                    >
                      <PlayIcon />
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="record-action-btn"
                      onClick={pauseRecording}
                      title="Pausar"
                    >
                      <PauseIcon />
                    </button>
                  )}
                  <button
                    type="button"
                    className="record-btn-main is-recording"
                    onClick={stopRecording}
                    title="Detener y guardar"
                    aria-label="Detener grabación"
                  >
                    <StopIcon />
                  </button>
                  <button
                    type="button"
                    className="record-action-btn"
                    onClick={discardRecording}
                    title="Descartar"
                  >
                    <TrashIcon />
                  </button>
                </div>
              </>
            )}

            {!isRecording && audioUrl && (
              <div className="record-preview-container">
                <p className="dropzone-text">
                  Grabación lista: <strong>{file?.name}</strong>
                </p>
                <audio src={audioUrl} controls className="record-preview-audio" />
                <div className="recording-controls" style={{ marginTop: '0.5rem' }}>
                  <button
                    type="button"
                    className="record-action-btn"
                    onClick={discardRecording}
                    disabled={isBusy}
                  >
                    <TrashIcon /> Descartar y volver a grabar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <button
        type="submit"
        className="submit-btn"
        disabled={isBusy || !file || isRecording}
      >
        {isBusy ? 'Procesando...' : 'Generar acta'}
      </button>
    </form>
  )
}

