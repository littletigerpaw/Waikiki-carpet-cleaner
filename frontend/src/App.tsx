import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import AccountPage from './pages/AccountPage'
import EmployeeHome from './pages/EmployeeHome'
import LoginPage from './pages/LoginPage'
import ManagerHome from './pages/ManagerHome'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute role="manager" />}>
            <Route path="/manager" element={<ManagerHome />} />
          </Route>

          <Route element={<ProtectedRoute role="employee" />}>
            <Route path="/employee" element={<EmployeeHome />} />
          </Route>

          {/* Any logged-in user */}
          <Route element={<ProtectedRoute />}>
            <Route path="/account" element={<AccountPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
