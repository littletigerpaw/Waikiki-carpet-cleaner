import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from '../api/client'
import { employee, manager, renderAt } from '../test/utils'
import LoginPage from './LoginPage'

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/client')>()
  return { ...actual, api: { ...actual.api, login: vi.fn(), me: vi.fn() } }
})

const loginRoute = <Route path="/login" element={<LoginPage />} />

async function fillAndSubmit(email: string, password: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText(/email/i), email)
  await user.type(screen.getByLabelText(/password/i), password)
  await user.click(screen.getByRole('button', { name: /sign in/i }))
  return user
}

describe('LoginPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('defaults to the employee portal', () => {
    renderAt('/login', loginRoute)
    expect(screen.getByRole('tab', { name: /employee login/i })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('button', { name: /sign in as employee/i })).toBeInTheDocument()
  })

  it('logs an employee in and sends them to the employee homepage', async () => {
    vi.mocked(api.login).mockResolvedValue({ token: 'tok', user: employee })
    renderAt('/login', loginRoute)

    await fillAndSubmit('lei@test.com', 'secret123')

    expect(api.login).toHaveBeenCalledWith('lei@test.com', 'secret123', 'employee')
    expect(await screen.findByRole('heading', { name: 'Employee Home' })).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBe('tok')
  })

  it('uses the manager portal when the Manager tab is selected', async () => {
    vi.mocked(api.login).mockResolvedValue({ token: 'tok', user: manager })
    renderAt('/login', loginRoute)

    await userEvent.setup().click(screen.getByRole('tab', { name: /manager login/i }))
    await fillAndSubmit('boss@test.com', 'secret123')

    expect(api.login).toHaveBeenCalledWith('boss@test.com', 'secret123', 'manager')
    expect(await screen.findByRole('heading', { name: 'Manager Home' })).toBeInTheDocument()
  })

  it('shows the server error message when login fails', async () => {
    vi.mocked(api.login).mockRejectedValue(new ApiError('Invalid email or password', 401))
    renderAt('/login', loginRoute)

    await fillAndSubmit('lei@test.com', 'wrong')

    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBeNull()
  })
})
