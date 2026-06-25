import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import UploadForm from './UploadForm'

describe('UploadForm drag-and-drop', () => {
  it('accepts a dropped audio file and shows its name', () => {
    render(<UploadForm onSubmit={vi.fn()} isBusy={false} />)

    const zone = screen.getByRole('button', { name: /arrastr/i })
    const file = new File(['audio'], 'meeting.wav', { type: 'audio/wav' })

    fireEvent.drop(zone, { dataTransfer: { files: [file] } })

    expect(screen.getByText('meeting.wav')).toBeTruthy()
  })

  it('ignores a dropped non-audio file', () => {
    render(<UploadForm onSubmit={vi.fn()} isBusy={false} />)

    const zone = screen.getByRole('button', { name: /arrastr/i })
    const file = new File(['x'], 'doc.pdf', { type: 'application/pdf' })

    fireEvent.drop(zone, { dataTransfer: { files: [file] } })

    expect(screen.queryByText('doc.pdf')).toBeNull()
  })
})

describe('UploadForm live recording', () => {
  beforeEach(() => {
    vi.restoreAllMocks()

    // Mock URL.createObjectURL and revokeObjectURL
    global.URL.createObjectURL = vi.fn().mockReturnValue('blob:http://localhost/test-recording')
    global.URL.revokeObjectURL = vi.fn()

    // Mock MediaRecorder
    const mediaRecorderMock = vi.fn().mockImplementation(() => {
      const instance = {
        state: 'inactive',
        mimeType: 'audio/webm',
        ondataavailable: null as any,
        onstop: null as any,
        start: vi.fn().mockImplementation(() => {
          instance.state = 'recording'
        }),
        stop: vi.fn().mockImplementation(() => {
          instance.state = 'inactive'
          if (instance.onstop) instance.onstop()
        }),
        pause: vi.fn(),
        resume: vi.fn(),
        addEventListener: vi.fn(),
      }
      return instance
    })

    // Assign properties to MediaRecorder
    Object.defineProperty(mediaRecorderMock, 'isTypeSupported', {
      value: vi.fn().mockReturnValue(true),
      writable: true,
    })

    global.MediaRecorder = mediaRecorderMock as any

    // Mock getUserMedia
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: vi.fn().mockReturnValue([{ stop: vi.fn() }]),
        }),
      },
      writable: true,
      configurable: true,
    })
  })

  it('switches tabs and displays recording prompt', () => {
    render(<UploadForm onSubmit={vi.fn()} isBusy={false} />)

    // Switch to recording tab
    const recordTab = screen.getByRole('button', { name: /grabar audio/i })
    fireEvent.click(recordTab)

    // Verify recording description is displayed
    expect(
      screen.getByText(/comenzar a grabar la reunión desde el navegador/i),
    ).toBeTruthy()

    // Verify record button is present
    expect(screen.getByRole('button', { name: /iniciar grabación/i })).toBeTruthy()
  })

  it('starts and stops recording, showing player preview', async () => {
    const { container } = render(<UploadForm onSubmit={vi.fn()} isBusy={false} />)

    // Switch to recording tab
    const recordTab = screen.getByRole('button', { name: /grabar audio/i })
    fireEvent.click(recordTab)

    // Start recording
    const startBtn = screen.getByRole('button', { name: /iniciar grabación/i })
    fireEvent.click(startBtn)

    // Verify record button is now a stop button
    const stopBtn = await screen.findByRole('button', { name: /detener grabación/i })
    expect(stopBtn).toBeTruthy()

    // Stop recording
    fireEvent.click(stopBtn)

    // Verify preview and audio element are rendered
    expect(await screen.findByText(/grabación lista/i)).toBeTruthy()
    expect(container.querySelector('audio')).toBeTruthy()
  })
})

