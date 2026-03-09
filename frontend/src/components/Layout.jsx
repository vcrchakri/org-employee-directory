import { Link } from "react-router-dom"

function Layout({ children }) {
  return (
    <div className="layout">

      {/* Sidebar */}
      <aside className="sidebar">
        <h2>Employee Directory</h2>

        <nav>
          <Link to="/home">Dashboard</Link>
          <Link to="/role-changes">Role Changes</Link>
          <Link to="/reports">Reports</Link>
        </nav>
      </aside>

      {/* Main content */}
      <main className="content">
        {children}
      </main>

    </div>
  )
}

export default Layout