let ctx: AudioContext | null = null

function getContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!Ctor) return null
  if (!ctx) ctx = new Ctor()
  return ctx
}

/** Call from a user gesture (the submit click) to satisfy autoplay policy. */
export function unlockAudio(): void {
  const c = getContext()
  if (c && c.state === 'suspended') void c.resume()
}

function beep(frequencies: number[], duration = 0.15): void {
  const c = getContext()
  if (!c) return
  if (c.state === 'suspended') void c.resume()
  let start = c.currentTime
  for (const freq of frequencies) {
    const osc = c.createOscillator()
    const gain = c.createGain()
    osc.type = 'sine'
    osc.frequency.value = freq
    gain.gain.setValueAtTime(0.0001, start)
    gain.gain.exponentialRampToValueAtTime(0.2, start + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration)
    osc.connect(gain).connect(c.destination)
    osc.start(start)
    osc.stop(start + duration)
    start += duration
  }
}

export function playDone(): void {
  beep([660, 880]) // pleasant rising two-tone
}

export function playError(): void {
  beep([300, 200]) // low descending tone
}
