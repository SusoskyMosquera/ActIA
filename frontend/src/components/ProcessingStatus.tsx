import type { AppState, ProcessingStage } from '../features/transcription/types'

interface ProcessingStatusProps {
  stage: ProcessingStage
  status: AppState
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

export default function ProcessingStatus({ stage, status }: ProcessingStatusProps) {
  return (
    <div className="processing-status" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p className="stage-label">{getStageLabel(stage, status)}</p>
      <p className="status-subtitle">Esto puede tardar unos minutos</p>
    </div>
  )
}
