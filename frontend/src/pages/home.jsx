import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiEmployees } from '../api/authApi.js'
import '../styles/Home.css'
import '../styles/homeNav.css'

function HomePage() {
  const navigate = useNavigate()
  const { member, signOut } = useAuth()

  const [menuOpen, setMenuOpen] = useState(false)
  const [employees, setEmployees] = useState([])

  const menuRef = useRef(null)

  // close dropdown when clicking outside
  useEffect(() => {
    function onDocMouseDown(e) {
      if (!menuRef.current) return
      if (!menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', onDocMouseDown)
    return () => document.removeEventListener('mousedown', onDocMouseDown)
  }, [])

  // fetch employees from backend
  useEffect(() => {
    async function loadEmployees() {
      try {
        const data = await apiEmployees()
        setEmployees(data || [])
      } catch (err) {
        console.error("Failed to fetch employees", err)
      }
    }

    loadEmployees()
  }, [])

  async function onLogout() {
    await signOut()
    navigate('/auth')
  }

  return (
    <div className="home-shell">

      {/* Top Bar */}
      <div className="home-topbar">
        <div className="dropdown" ref={menuRef}>
          <button
            className="home-userbtn"
            type="button"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <i className="bi bi-person-circle" />
          </button>

          <ul className={`dropdown-menu dropdown-menu-end home-dropdown ${menuOpen ? 'show' : ''}`}>

            <li className="px-3 pt-2 pb-1">
              <div className="home-userline">
                <i className="bi bi-person-circle" />
                <div>
                  <div className="home-username">{member?.name || '--'}</div>
                  <div className="home-userdetail">{member?.email || '--'}</div>
                  <div className="home-userdetail">{member?.phone || '--'}</div>
                </div>
              </div>
            </li>

            <li>
              <hr className="dropdown-divider" />
            </li>

            <li className="px-3 pb-3">
              <button
                className="btn btn-danger w-100"
                type="button"
                onClick={onLogout}
              >
                Logout
              </button>
            </li>

          </ul>
        </div>
      </div>


      {/* Main Content */}
      <main className="home-center" aria-live="polite">

        <h1 className="home-title">Welcome to Hackathon</h1>
        <p className="home-subtitle">
          This is your starting point of your hackathon.
        </p>

        {/* Employee Count */}
        <div style={{ marginBottom: "25px", fontWeight: "bold" }}>
          Total Employees: {employees.length}
        </div>

        {/* Navigation Cards */}
        <div className="hn-grid">

          <button
            className="hn-card"
            onClick={() => navigate('/role-changes')}
          >
            <i className="bi bi-arrow-repeat hn-icon" />
            <div className="hn-label">
              Job / Role Change Tracking
            </div>
            <div className="hn-desc">
              Record CTC, role & level changes with date history
            </div>
          </button>

          <button
            className="hn-card"
            onClick={() => navigate('/reports')}
          >
            <i className="bi bi-bar-chart-line hn-icon" />
            <div className="hn-label">
              Joiners & Leavers Report
            </div>
            <div className="hn-desc">
              Monthly hiring and attrition metrics
            </div>
          </button>

        </div>

      </main>
    </div>
  )
}

export default HomePage