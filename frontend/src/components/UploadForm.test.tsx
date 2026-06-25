import { describe, it, expect, vi } from 'vitest'
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
