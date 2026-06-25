import ReactMarkdown from 'react-markdown'
import type { JobResult } from '../features/transcription/types'
import { formatClock, formatDuration } from '../lib/format'
import ExportMenu from './ExportMenu'

interface MinutesResultProps {
  result: JobResult
}

export default function MinutesResult({ result }: MinutesResultProps) {
  const { transcript, minutes, metadata } = result

  return (
    <div className="minutes-result">
      <ExportMenu result={result} />

      <div className="result-section">
        <h2>Detalles</h2>
        <div className="metadata-grid">
          <div className="metadata-item">
            <div className="meta-label">Duración</div>
            <div className="meta-value">{formatDuration(metadata.duration_sec)}</div>
          </div>
          <div className="metadata-item">
            <div className="meta-label">Idioma</div>
            <div className="meta-value">{metadata.language.toUpperCase()}</div>
          </div>
          <div className="metadata-item">
            <div className="meta-label">Oradores</div>
            <div className="meta-value">{metadata.num_speakers}</div>
          </div>
          <div className="metadata-item">
            <div className="meta-label">Modelo</div>
            <div className="meta-value">{metadata.model}</div>
          </div>
        </div>
      </div>

      <div className="result-section">
        <h2>Acta de la reunión</h2>
        <div className="markdown-content">
          <ReactMarkdown>{minutes}</ReactMarkdown>
        </div>
      </div>

      <div className="result-section">
        <h2>Transcripción</h2>
        <ul className="transcript-list">
          {transcript.map((segment, index) => (
            <li key={index} className="transcript-item">
              <span className="speaker-tag">{segment.speaker}</span>
              <span className="transcript-text">{segment.text}</span>
              <span className="transcript-time">
                {formatClock(segment.start)} — {formatClock(segment.end)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
