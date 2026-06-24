import TranscriptionContainer from './features/transcription/TranscriptionContainer'

function App() {
  return (
    <main className="app">
      <header className="app-header">
        <h1>ActIA</h1>
        <p>Meeting Minutes Generator</p>
      </header>
      <TranscriptionContainer />
    </main>
  )
}

export default App
