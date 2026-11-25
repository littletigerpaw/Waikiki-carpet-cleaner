import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { Role } from '../types'
import { homePathFor } from '../utils'

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()

  const [role, setRole] = useState<Role>('employee')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Already logged in? Send them to their homepage.
  if (user) return <Navigate to={homePathFor(user.role)} replace />

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const loggedIn = await login(email, password, role)
      navigate(homePathFor(loggedIn.role), { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <span className="brand-mark brand-mark-lg">W</span>
          <h1>Waikiki Carpet Cleaners</h1>
          <p className="muted">Vacation rental cleaning portal</p>
        </div>

        <div className="role-toggle" role="tablist">
          {(['employee', 'manager'] as Role[]).map((r) => (
            <button
              key={r}
              type="button"
              role="tab"
              aria-selected={role === r}
              className={role === r ? 'active' : ''}
              onClick={() => {
                setRole(r)
                setError('')
              }}
            >
              {r === 'manager' ? 'Manager' : 'Employee'} Login
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="form">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@waikiki.com"
              autoComplete="email"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && <p className="error">{error}</p>}

          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? 'Signing in…' : `Sign in as ${role === 'manager' ? 'Manager' : 'Employee'}`}
          </button>
        </form>
      </div>
    </div>
  )
}
