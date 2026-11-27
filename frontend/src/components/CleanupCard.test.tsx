import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import CleanupCard from './CleanupCard'

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/client')>()
  return { ...actual, api: { ...actual.api, cleanupPreview: vi.fn(), cleanupOldTasks: vi.fn() } }
})

const summary = (days: number, tasks: number, photos: number) => ({ days, cutoff: '2026-08-29', tasks, photos })

describe('CleanupCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.cleanupPreview).mockImplementation(async (days) => summary(days, days === 90 ? 3 : 0, 5))
  })
  afterEach(() => vi.restoreAllMocks())

  it('shows how much will be deleted before deleting anything', async () => {
    render(<CleanupCard refreshKey={0} onDeleted={vi.fn()} />)
    expect(await screen.findByRole('button', { name: 'Delete 3 tasks & 5 photos' })).toBeEnabled()
    expect(api.cleanupPreview).toHaveBeenCalledWith(90)
    expect(api.cleanupOldTasks).not.toHaveBeenCalled()
  })

  it('disables the button when there is nothing to delete', async () => {
    render(<CleanupCard refreshKey={0} onDeleted={vi.fn()} />)
    await screen.findByRole('button', { name: /delete 3 tasks/i })
    await userEvent.setup().selectOptions(screen.getByRole('combobox'), '365')
    expect(await screen.findByRole('button', { name: 'Nothing to delete' })).toBeDisabled()
  })

  it('does nothing if the manager cancels the confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<CleanupCard refreshKey={0} onDeleted={vi.fn()} />)
    await userEvent.setup().click(await screen.findByRole('button', { name: /delete 3 tasks/i }))
    expect(window.confirm).toHaveBeenCalled()
    expect(api.cleanupOldTasks).not.toHaveBeenCalled()
  })

  it('deletes after confirmation and reports the result', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.cleanupOldTasks).mockResolvedValue(summary(90, 3, 5))
    const onDeleted = vi.fn()
    render(<CleanupCard refreshKey={0} onDeleted={onDeleted} />)

    await userEvent.setup().click(await screen.findByRole('button', { name: /delete 3 tasks/i }))

    expect(api.cleanupOldTasks).toHaveBeenCalledWith(90)
    await waitFor(() => expect(onDeleted).toHaveBeenCalledWith('Deleted 3 old tasks and 5 photos.'))
  })
})
