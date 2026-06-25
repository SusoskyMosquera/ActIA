import UploadForm from '../../components/UploadForm'
import ProcessingStatus from '../../components/ProcessingStatus'
import MinutesResult from '../../components/MinutesResult'
import ErrorBanner from '../../components/ErrorBanner'
import { useTranscriptionJob } from './hooks/useTranscriptionJob'
import type { TranscriptionOptions } from './types'

export default function TranscriptionContainer() {
  const { state, stage, result, error, submit, reset, cancel } = useTranscriptionJob()

  const isBusy = state === 'submitting' || state === 'processing'

  const handleSubmit = (file: File, opts: TranscriptionOptions) => {
    void submit(file, opts)
  }

  return (
    <div>
      <UploadForm onSubmit={handleSubmit} isBusy={isBusy} />

      {(state === 'submitting' || state === 'processing') && (
        <>
          <ProcessingStatus stage={stage} status={state} />
          <button className="cancel-btn" onClick={() => void cancel()}>
            Cancelar
          </button>
        </>
      )}

      {state === 'done' && result !== null && (
        <>
          <MinutesResult result={result} />
          <button className="submit-btn" style={{ marginTop: '1rem' }} onClick={reset}>
            Procesar otra grabación
          </button>
        </>
      )}

      {state === 'error' && error !== null && (
        <>
          <ErrorBanner message={error} />
          <button className="submit-btn" onClick={reset}>
            Reintentar
          </button>
        </>
      )}
    </div>
  )
}
