import { Navigate, Route, Routes } from 'react-router-dom'
import AuthPage from './pages/auth.jsx'
import HomePage from './pages/home.jsx'
import RoleChangesPage from './pages/RoleChanges.jsx'
import ReportsPage from './pages/Reports.jsx'
import RequireAuth from './auth/RequireAuth.jsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/auth" replace />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/home"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />
      <Route
        path="/role-changes"
        element={
          <RequireAuth>
            <RoleChangesPage />
          </RequireAuth>
        }
      />
      <Route
        path="/reports"
        element={
          <RequireAuth>
            <ReportsPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/auth" replace />} />
    </Routes>
  )
}

export default App
