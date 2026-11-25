import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { Role } from '../types'
import { homePathFor } from '../utils'

/**
 * Only lets logged-in users through. If `role` is given, only that role;
 * everyone else is redirected to their own homepage.
 */
export default function ProtectedRoute({ role }: { role?: Role }) {
  const { user, loading } = useAuth()

  if (loading) return <div className="center-screen">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) return <Navigate to={homePathFor(user.role)} replace />

  return <Outlet />
}
