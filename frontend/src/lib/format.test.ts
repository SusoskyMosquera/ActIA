import { describe, it, expect } from 'vitest'
import { formatClock, formatDuration } from './format'

describe('formatClock', () => {
  it('formats seconds as zero-padded mm:ss', () => {
    expect(formatClock(0)).toBe('00:00')
    expect(formatClock(5)).toBe('00:05')
    expect(formatClock(65)).toBe('01:05')
    expect(formatClock(600)).toBe('10:00')
  })

  it('floors fractional seconds', () => {
    expect(formatClock(4.9)).toBe('00:04')
  })
})

describe('formatDuration', () => {
  it('shows only seconds under a minute', () => {
    expect(formatDuration(5)).toBe('5s')
    expect(formatDuration(0)).toBe('0s')
  })

  it('shows minutes and seconds at or above a minute', () => {
    expect(formatDuration(65)).toBe('1m 5s')
    expect(formatDuration(125)).toBe('2m 5s')
  })
})
