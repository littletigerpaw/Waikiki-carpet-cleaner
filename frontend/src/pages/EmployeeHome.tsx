import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Navbar from '../components/Navbar'
import PhotoGallery from '../components/PhotoGallery'
import StatusBadge from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import { STATUS_LABELS } from '../types'
import type { Task, TaskPhoto, TaskStatus } from '../types'

export default function EmployeeHome() {
  const { user } = useAuth()
  const [tasks, setTasks] = useState<Task[] | null>(null)
  const [error, setError] = useState('')
  const [uploadingId, setUploadingId] = useState<number | null>(null)
  const [today] = useState(() => new Date().toLocaleDateString('en-CA')) // YYYY-MM-DD, local time

  useEffect(() => {
    api.myTasks().then(setTasks).catch((e: Error) => setError(e.message))
  }, [])

  const changeStatus = async (task: Task, status: TaskStatus) => {
    try {
      const updated = await api.updateTaskStatus(task.id, status)
      replaceTask(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update task')
    }
  }

  const replaceTask = (updated: Task) =>
    setTasks((prev) => prev?.map((t) => (t.id === updated.id ? updated : t)) ?? null)

  const handleUpload = async (task: Task, files: FileList | null) => {
    if (!files || files.length === 0) return
    setError('')
    setUploadingId(task.id)
    try {
      replaceTask(await api.uploadPhotos(task.id, files))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploadingId(null)
    }
  }

  const handleDeletePhoto = async (task: Task, photo: TaskPhoto) => {
    if (!window.confirm('Delete this photo?')) return
    try {
      replaceTask(await api.deletePhoto(task.id, photo.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete photo')
    }
  }

  const todays = tasks?.filter((t) => t.scheduled_date === today) ?? []
  const upcoming = tasks?.filter((t) => t.scheduled_date !== today) ?? []

  const renderTasks = (list: Task[], emptyText: string) =>
    list.length === 0 ? (
      <p className="muted">{emptyText}</p>
    ) : (
      <div className="task-grid">
        {list.map((t) => (
          <article key={t.id} className="task-card">
            <div className="task-top">
              <h4>{t.unit_name}</h4>
              <StatusBadge status={t.status} />
            </div>
            <p className="small">📍 {t.address}</p>
            <p className="small">📅 {t.scheduled_date}</p>
            {t.description && <p className="small muted">{t.description}</p>}
            <label className="small">
              Update status
              <select value={t.status} onChange={(e) => changeStatus(t, e.target.value as TaskStatus)}>
                {(Object.keys(STATUS_LABELS) as TaskStatus[]).map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            </label>

            <div className="photo-section">
              <strong className="small">Photos</strong>
              <PhotoGallery photos={t.photos} onDelete={(p) => handleDeletePhoto(t, p)} />
              {uploadingId === t.id ? (
                <p className="muted small">Uploading…</p>
              ) : (
                <div className="upload-actions">
                  {/* Phones/tablets only: opens the rear camera directly */}
                  <label className="btn btn-primary btn-sm upload-btn camera-only">
                    📸 Take photo
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      hidden
                      onChange={(e) => {
                        handleUpload(t, e.target.files)
                        e.target.value = ''
                      }}
                    />
                  </label>
                  {/* Photo library / files (phones also offer the camera here) */}
                  <label className="btn btn-outline btn-sm upload-btn">
                    🖼️ Choose photos
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      hidden
                      onChange={(e) => {
                        handleUpload(t, e.target.files)
                        e.target.value = '' // allow re-selecting the same file
                      }}
                    />
                  </label>
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    )

  return (
    <>
      <Navbar />
      <main className="container">
        <h2>Aloha, {user?.first_name} 🌺</h2>
        <p className="muted">Here are your assigned cleanings.</p>

        {error && <p className="error">{error}</p>}
        {!tasks && !error && <p className="muted">Loading…</p>}

        {tasks && (
          <>
            <section className="card">
              <h3>Today</h3>
              {renderTasks(todays, 'No cleanings scheduled for today.')}
            </section>
            <section className="card">
              <h3>Upcoming &amp; Past</h3>
              {renderTasks(upcoming, 'Nothing else on your schedule.')}
            </section>
          </>
        )}
      </main>
    </>
  )
}
