import { Link } from "react-router-dom"

function Layout({ children }) {
  return (
    <div className="app-container">

      <aside className="sidebar">
        <h2>Employee Directory</h2>

        <nav>
          <Link to="/home">Employees</Link>
          <Link to="/reports">Reports</Link>
          <Link to="/role-changes">Role Changes</Link>
        </nav>
      </aside>

      <main className="main-content">
        {children}
      </main>

    </div>
  )
}

export default Layout