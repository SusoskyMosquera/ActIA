import TranscriptionContainer from './features/transcription/TranscriptionContainer'

function App() {
  return (
    <main className="app">
      <header className="app-header">
        <h1>ActIA</h1>
        <p>Generador de Actas de Reunión</p>
      </header>
      <TranscriptionContainer />
    </main>
  )
}

export default App
