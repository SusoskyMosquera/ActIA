import ReactMarkdown from 'react-markdown'
import type { JobResult } from '../features/transcription/types'

interface MinutesResultProps {
  result: JobResult
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

export default function MinutesResult({ result }: MinutesResultProps) {
  const { transcript, minutes, metadata } = result

  return (
    <div className="minutes-result">
      <div className="result-section">
        <h2>Metadata</h2>
        <div className="metadata-grid">
          <div className="metadata-item">
            <div className="meta-label">Duration</div>
            <div className="meta-value">{formatDuration(metadata.duration_sec)}</div>
          </div>
          <div className="metadata-item">
            <div className="meta-label">Language</div>
            <div className="meta-value">{metadata.language.toUpperCase()}</div>
          </div>
          <div className="metadata-item">
            <div className="meta-label">Speakers</div>
            <div className="meta-value">{metadata.num_speakers}</div>
          </div>
          <div className="metadata-item">
            <div className="meta-label">Model</div>
            <div className="meta-value">{metadata.model}</div>
          </div>
        </div>
      </div>

      <div className="result-section">
        <h2>Meeting Minutes</h2>
        <div className="markdown-content">
          <ReactMarkdown>{minutes}</ReactMarkdown>
        </div>
      </div>

      <div className="result-section">
        <h2>Transcript</h2>
        <ul className="transcript-list">
          {transcript.map((segment, index) => (
            <li key={index} className="transcript-item">
              <span className="speaker-tag">{segment.speaker}</span>
              <span className="transcript-text">{segment.text}</span>
              <span className="transcript-time">
                {formatTime(segment.start)} — {formatTime(segment.end)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
