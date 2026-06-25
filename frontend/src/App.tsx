import TranscriptionContainer from './features/transcription/TranscriptionContainer'

function App() {
  return (
    <main className="app">
      <header className="app-header">
        <h1 className="app-title">
          <img src="/logo.png" alt="ActIA" className="app-logo" />
        </h1>
        <p>Generador de Actas de Reunión</p>
      </header>
      <TranscriptionContainer />
    </main>
  )
}

export default App
