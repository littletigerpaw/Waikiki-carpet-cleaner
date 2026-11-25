import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api/client'
import { STATUS_LABELS } from '../types'
import type { Task, TaskStatus, User } from '../types'
import PhotoGallery from './PhotoGallery'

interface Props {
  task: Task
  employees: User[]
  onClose: () => void
  onSaved: () => void
}

/** Manager popup to edit, reassign, or delete a task and view its photos. */
export default function EditTaskModal({ task, employees, onClose, onSaved }: Props) {
  const [form, setForm] = useState({
    unit_name: task.unit_name,
    address: task.address,
    description: task.description ?? '',
    scheduled_date: task.scheduled_date,
    assigned_to_id: task.assigned_to ? String(task.assigned_to.id) : '',
    status: task.status,
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  // Close on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const handleSave = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await api.updateTask(task.id, {
        ...form,
        assigned_to_id: form.assigned_to_id ? Number(form.assigned_to_id) : null,
      })
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save task')
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${task.unit_name}"? This also deletes its photos and cannot be undone.`)) return
    setSaving(true)
    try {
      await api.deleteTask(task.id)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete task')
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Edit Task</h3>
          <button className="icon-btn" aria-label="Close" onClick={onClose}>×</button>
        </div>

        <form className="form" onSubmit={handleSave}>
          <label>
            Unit name
            <input required value={form.unit_name}
              onChange={(e) => setForm({ ...form, unit_name: e.target.value })} />
          </label>
          <label>
            Address
            <input required value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </label>
          <label>
            Notes
            <textarea rows={2} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </label>
          <div className="row">
            <label>
              Date
              <input type="date" required value={form.scheduled_date}
                onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} />
            </label>
            <label>
              Status
              <select value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as TaskStatus })}>
                {(Object.keys(STATUS_LABELS) as TaskStatus[]).map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Assigned to
            <select value={form.assigned_to_id}
              onChange={(e) => setForm({ ...form, assigned_to_id: e.target.value })}>
              <option value="">Unassigned</option>
              {employees
                // Only active employees, plus the current assignee so history stays visible
                .filter((emp) => emp.is_active || emp.id === task.assigned_to?.id)
                .map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.first_name} {emp.last_name}{emp.is_active ? '' : ' (deactivated)'}
                  </option>
                ))}
            </select>
          </label>

          <div>
            <strong className="small">Photos ({task.photos.length})</strong>
            <PhotoGallery photos={task.photos} />
          </div>

          {error && <p className="error">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn btn-danger" onClick={handleDelete} disabled={saving}>
              Delete Task
            </button>
            <div className="spacer" />
            <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
