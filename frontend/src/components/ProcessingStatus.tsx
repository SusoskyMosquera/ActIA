import type { AppState, ProcessingStage } from '../features/transcription/types'

interface ProcessingStatusProps {
  stage: ProcessingStage
  status: AppState
}

const STAGE_LABELS: Record<NonNullable<ProcessingStage>, string> = {
  TRANSCRIBING: 'Transcribing audio...',
  DIARIZING: 'Identifying speakers...',
  GENERATING_MINUTES: 'Generating meeting minutes...',
}

function getStageLabel(stage: ProcessingStage, status: AppState): string {
  if (stage !== null && stage in STAGE_LABELS) {
    return STAGE_LABELS[stage]
  }
  if (status === 'submitting') return 'Uploading audio file...'
  return 'Processing...'
}

export default function ProcessingStatus({ stage, status }: ProcessingStatusProps) {
  return (
    <div className="processing-status" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p className="stage-label">{getStageLabel(stage, status)}</p>
      <p className="status-subtitle">This may take a few minutes</p>
    </div>
  )
}
