import { screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from '../api/client'
import { employee, manager, renderAt } from '../test/utils'
import ProtectedRoute from './ProtectedRoute'

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/client')>()
  return { ...actual, api: { ...actual.api, me: vi.fn() } }
})

const routes = (
  <>
    <Route path="/login" element={<h1>Login Page</h1>} />
    <Route element={<ProtectedRoute role="manager" />}>
      <Route path="/secret-manager" element={<h1>Manager Only</h1>} />
    </Route>
    <Route element={<ProtectedRoute />}>
      <Route path="/account" element={<h1>Account</h1>} />
    </Route>
  </>
)

describe('ProtectedRoute', () => {
  beforeEach(() => vi.clearAllMocks())

  it('sends logged-out visitors to the login page', async () => {
    renderAt('/secret-manager', routes)
    expect(await screen.findByRole('heading', { name: 'Login Page' })).toBeInTheDocument()
    expect(api.me).not.toHaveBeenCalled()
  })

  it('lets a manager into a manager page', async () => {
    localStorage.setItem('token', 'tok')
    vi.mocked(api.me).mockResolvedValue(manager)
    renderAt('/secret-manager', routes)
    expect(await screen.findByRole('heading', { name: 'Manager Only' })).toBeInTheDocument()
  })

  it('redirects an employee away from a manager page to their own home', async () => {
    localStorage.setItem('token', 'tok')
    vi.mocked(api.me).mockResolvedValue(employee)
    renderAt('/secret-manager', routes)
    expect(await screen.findByRole('heading', { name: 'Employee Home' })).toBeInTheDocument()
    expect(screen.queryByText('Manager Only')).not.toBeInTheDocument()
  })

  it('allows any logged-in role on pages without a role', async () => {
    localStorage.setItem('token', 'tok')
    vi.mocked(api.me).mockResolvedValue(employee)
    renderAt('/account', routes)
    expect(await screen.findByRole('heading', { name: 'Account' })).toBeInTheDocument()
  })

  it('clears an invalid saved token and goes to login', async () => {
    localStorage.setItem('token', 'expired')
    vi.mocked(api.me).mockRejectedValue(new ApiError('Session expired', 401))
    renderAt('/account', routes)
    expect(await screen.findByRole('heading', { name: 'Login Page' })).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBeNull()
  })
})
