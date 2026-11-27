import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { CleanupSummary } from '../types'

const AGE_OPTIONS = [
  { days: 30, label: '30 days' },
  { days: 60, label: '60 days' },
  { days: 90, label: '90 days' },
  { days: 180, label: '6 months' },
  { days: 365, label: '1 year' },
]

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`

interface Props {
  /** Bump this number to re-check the preview (e.g. after tasks change) */
  refreshKey: number
  onDeleted: (message: string) => void
}

/** Manager tool: permanently delete old completed tasks and their photos to free up storage. */
export default function CleanupCard({ refreshKey, onDeleted }: Props) {
  const [days, setDays] = useState(90)
  const [preview, setPreview] = useState<CleanupSummary | null>(null)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let cancelled = false
    api
      .cleanupPreview(days)
      .then((p) => !cancelled && (setPreview(p), setError('')))
      .catch((e: Error) => !cancelled && setError(e.message))
    return () => {
      cancelled = true
    }
  }, [days, refreshKey])

  // Only trust the preview if it matches the currently selected age
  const current = preview?.days === days ? preview : null

  const handleDelete = async () => {
    if (!current || current.tasks === 0) return
    const what = `${plural(current.tasks, 'completed task')} and ${plural(current.photos, 'photo')}`
    if (!window.confirm(`Permanently delete ${what} from before ${current.cutoff}?\n\nThis cannot be undone.`)) return

    setDeleting(true)
    setError('')
    try {
      const res = await api.cleanupOldTasks(days)
      onDeleted(`Deleted ${plural(res.tasks, 'old task')} and ${plural(res.photos, 'photo')}.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Clean-up failed')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <section className="card cleanup-card">
      <h3>Clean Up Old Data</h3>
      <p className="muted small">
        Permanently delete <strong>completed</strong> cleanings (and their photos) to free up storage.
        Pending and in-progress tasks are never touched.
      </p>

      <div className="cleanup-row">
        <label className="small">
          Completed more than
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            {AGE_OPTIONS.map((o) => (
              <option key={o.days} value={o.days}>{o.label}</option>
            ))}
          </select>
          ago
        </label>

        <button
          type="button"
          className="btn btn-danger"
          onClick={handleDelete}
          disabled={deleting || !current || current.tasks === 0}
        >
          {deleting
            ? 'Deleting…'
            : !current
              ? 'Checking…'
              : current.tasks === 0
                ? 'Nothing to delete'
                : `Delete ${plural(current.tasks, 'task')} & ${plural(current.photos, 'photo')}`}
        </button>
      </div>

      {current && current.tasks > 0 && (
        <p className="small muted">Cleanings dated before {current.cutoff}.</p>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  )
}
