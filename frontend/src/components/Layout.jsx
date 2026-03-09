import { Link, Outlet } from "react-router-dom"

function Layout() {
  return (
    <div className="app-shell">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="sidebar-brand">
          <div className="brand-icon">👥</div>
          <span className="brand-name">Employee Directory</span>
        </div>

        {/* Headcount Section */}
        <div className="sidebar-section">
          <p className="section-label">Headcount</p>

          <div className="headcount-row">
            <div className="hc-stat">
              <span className="number active">2</span>
              <span className="lbl">Active</span>
            </div>

            <div className="hc-stat">
              <span className="number exited">0</span>
              <span className="lbl">Exited</span>
            </div>
          </div>
        </div>

        {/* Manage Employee */}
        <div className="sidebar-section">
          <p className="section-label">Manage Employee</p>

          <div className="form-fields">

            <input
              className="field-input"
              placeholder="Emp ID (EMP001)"
            />

            <input
              className="field-input"
              placeholder="Full Name"
            />

            <input
              className="field-input"
              type="date"
            />

            <input
              className="field-input"
              placeholder="Role"
            />

            <input
              className="field-input"
              type="date"
              placeholder="Exit Date"
            />

          </div>

          <div className="btn-group">

            <button className="btn btn-primary btn-block">
              + Create Employee
            </button>

            <button className="btn btn-secondary btn-block">
              Update Details
            </button>

            <button className="btn btn-danger btn-block">
              Exit Employee
            </button>

          </div>
        </div>

        {/* Quick Links */}
        <div className="sidebar-section">
          <p className="section-label">Quick Links</p>

          <div className="quick-links">

            <Link to="/home" className="sidebar-btn blue">
              Onboarding Tracker
            </Link>

            <Link to="/reports" className="sidebar-btn green">
              Joiners & Leavers
            </Link>

            <Link to="/role-changes" className="sidebar-btn yellow">
              Role Tracking
            </Link>

          </div>
        </div>

      </aside>

      {/* MAIN CONTENT */}
      <main className="main">
        <Outlet />
      </main>

    </div>
  )
}

export default Layout