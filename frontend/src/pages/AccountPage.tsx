import { useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api/client'
import Navbar from '../components/Navbar'
import { useAuth } from '../context/AuthContext'

const MIN_LENGTH = 8
const empty = { current: '', next: '', confirm: '' }

export default function AccountPage() {
  const { user } = useAuth()
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (form.next.length < MIN_LENGTH) return setError(`New password must be at least ${MIN_LENGTH} characters.`)
    if (form.next !== form.confirm) return setError('New passwords do not match.')

    setSaving(true)
    try {
      await api.changePassword(form.current, form.next)
      setForm(empty)
      setSuccess('Password updated. Use your new password next time you log in.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not change password')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <Navbar />
      <main className="container narrow">
        <h2>My Account</h2>

        <section className="card">
          <h3>Profile</h3>
          <dl className="profile">
            <dt>Name</dt><dd>{user?.first_name} {user?.last_name}</dd>
            <dt>Email</dt><dd>{user?.email}</dd>
            <dt>Phone</dt><dd>{user?.phone || '—'}</dd>
            <dt>Role</dt><dd className="capitalize">{user?.role}</dd>
          </dl>
        </section>

        <section className="card">
          <h3>Change Password</h3>
          <form className="form" onSubmit={handleSubmit}>
            <label>
              Current password
              <input type="password" required autoComplete="current-password" value={form.current}
                onChange={(e) => setForm({ ...form, current: e.target.value })} />
            </label>
            <label>
              New password
              <input type="password" required autoComplete="new-password" minLength={MIN_LENGTH} value={form.next}
                onChange={(e) => setForm({ ...form, next: e.target.value })} />
              <span className="muted small">At least {MIN_LENGTH} characters.</span>
            </label>
            <label>
              Confirm new password
              <input type="password" required autoComplete="new-password" value={form.confirm}
                onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
            </label>

            {error && <p className="error">{error}</p>}
            {success && <p className="notice">{success}</p>}

            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Updating…' : 'Update Password'}
            </button>
          </form>
        </section>
      </main>
    </>
  )
}
