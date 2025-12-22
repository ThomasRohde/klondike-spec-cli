import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './components/Dashboard'
import { SpecExplorer } from './components/SpecExplorer'
import { ActivityLog } from './components/ActivityLog'
import { ConfigEditor } from './components/ConfigEditor'
import { TaskViewer } from './components/TaskViewer'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="specs" element={<SpecExplorer />} />
          <Route path="task/:featureId" element={<TaskViewer />} />
          <Route path="activity" element={<ActivityLog />} />
          <Route path="config" element={<ConfigEditor />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
