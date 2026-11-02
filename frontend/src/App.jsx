import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Analyzer from './pages/Analyzer'
import SourceCredibility from './pages/SourceCredibility'
import HistoryPage from './pages/HistoryPage'
import ModelPerformance from './pages/ModelPerformance'
import About from './pages/About'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/app" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="analyze" element={<Analyzer />} />
        <Route path="source" element={<SourceCredibility />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="history/:id" element={<HistoryPage />} />
        <Route path="models" element={<ModelPerformance />} />
        <Route path="about" element={<About />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
