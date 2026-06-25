/** Read an audio file's duration (ms) client-side. Resolves null if unknown/undecodable. */
export function getAudioDurationMs(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || typeof Audio === 'undefined') {
      resolve(null)
      return
    }
    // URL.createObjectURL may be absent in test environments (jsdom)
    if (typeof URL === 'undefined' || typeof URL.createObjectURL !== 'function') {
      resolve(null)
      return
    }
    let url: string
    try {
      url = URL.createObjectURL(file)
    } catch {
      resolve(null)
      return
    }
    // `url` is guaranteed to be assigned here — the catch block always returns
    const objectUrl = url
    const audio = new Audio()
    const done = (value: number | null) => {
      URL.revokeObjectURL(objectUrl)
      resolve(value)
    }
    audio.addEventListener('loadedmetadata', () =>
      done(Number.isFinite(audio.duration) ? audio.duration * 1000 : null),
    )
    audio.addEventListener('error', () => done(null))
    audio.src = objectUrl
  })
}
