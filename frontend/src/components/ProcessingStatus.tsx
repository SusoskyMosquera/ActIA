import type { AppState, ProcessingStage } from '../features/transcription/types'

interface ProcessingStatusProps {
  stage: ProcessingStage
  status: AppState
  progress: number | null
}

const STAGE_LABELS: Record<NonNullable<ProcessingStage>, string> = {
  ANALYZING: 'Analizando el audio (transcripción y oradores)...',
  TRANSCRIBING: 'Transcribiendo el audio...',
  DIARIZING: 'Identificando oradores...',
  GENERATING_MINUTES: 'Generando el acta...',
}

function getStageLabel(stage: ProcessingStage, status: AppState): string {
  if (stage !== null && stage in STAGE_LABELS) {
    return STAGE_LABELS[stage]
  }
  if (status === 'submitting') return 'Subiendo el archivo de audio...'
  return 'Procesando...'
}

export default function ProcessingStatus({ stage, status, progress }: ProcessingStatusProps) {
  const isIndeterminate = progress === null

  return (
    <div className="processing-status" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p className="stage-label">{getStageLabel(stage, status)}</p>

      <div className="progress-track">
        <div
          className={`progress-fill${isIndeterminate ? ' progress-fill--indeterminate' : ''}`}
          style={!isIndeterminate ? { width: `${Math.round(progress * 100)}%` } : undefined}
          role="progressbar"
          aria-valuenow={!isIndeterminate ? Math.round(progress * 100) : undefined}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      <p className="status-subtitle">Esto puede tardar unos minutos</p>
    </div>
  )
}
