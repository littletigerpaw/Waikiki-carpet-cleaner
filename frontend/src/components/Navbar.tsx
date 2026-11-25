import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { homePathFor } from '../utils'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="navbar">
      <div className="brand">
        <span className="brand-mark">W</span>
        <span>Waikiki Carpet Cleaners</span>
      </div>
      {user && (
        <>
          <nav className="nav-links">
            <NavLink to={homePathFor(user.role)}>Home</NavLink>
            <NavLink to="/account">My Account</NavLink>
          </nav>
          <div className="nav-right">
            <span className="nav-user">
              {user.first_name} {user.last_name}
              <span className={`role-badge role-${user.role}`}>{user.role}</span>
            </span>
            <button className="btn btn-outline" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </>
      )}
    </header>
  )
}
