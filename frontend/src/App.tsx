import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import SubmitPage from './pages/SubmitPage'
import DashboardPage from './pages/DashboardPage'
import ErrorBoundary from './components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="app">
          <nav className="navbar">
            <div className="nav-brand">CivicPulse</div>
            <div className="nav-links">
              <Link to="/">Submit</Link>
              <Link to="/dashboard">Dashboard</Link>
            </div>
          </nav>
          <main className="main-content">
            <Routes>
              <Route path="/" element={<SubmitPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
