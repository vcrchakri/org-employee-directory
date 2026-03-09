import { BrowserRouter, Routes, Route } from "react-router-dom"
import Layout from "./components/Layout"
import HomePage from "./pages/home"
import Reports from "./pages/Reports"
import RoleChanges from "./pages/RoleChanges"

function App() {
  return (
    <BrowserRouter>

      <Routes>

        <Route element={<Layout />}>

          <Route path="/" element={<HomePage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/role-changes" element={<RoleChanges />} />

        </Route>

      </Routes>

    </BrowserRouter>
  )
}

export default App