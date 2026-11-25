import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import type { User } from '../types'

export const manager: User = {
  id: 1, first_name: 'Kai', last_name: 'Boss', email: 'boss@test.com', phone: null, role: 'manager', is_active: true,
}
export const employee: User = {
  id: 2, first_name: 'Lei', last_name: 'Worker', email: 'lei@test.com', phone: null, role: 'employee', is_active: true,
}

/** Render routes inside the real AuthProvider + a router starting at `path`. */
export function renderAt(path: string, routes: ReactElement) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          {routes}
          <Route path="/manager" element={<h1>Manager Home</h1>} />
          <Route path="/employee" element={<h1>Employee Home</h1>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}
