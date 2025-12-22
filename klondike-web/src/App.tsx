import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Layout } from './components/Layout'
import { Dashboard } from './components/Dashboard'
import { SpecExplorer } from './components/SpecExplorer'
import { ActivityLog } from './components/ActivityLog'
import { ConfigEditor } from './components/ConfigEditor'
import { TaskViewer } from './components/TaskViewer'
import { KanbanBoard } from './components/KanbanBoard'
import { CommandPalette } from './components/CommandPalette'
import { useCommandPalette } from './hooks/useCommandPalette'
import { ShortcutsHelpOverlay, ShortcutsHelpButton } from './components/ShortcutsHelp'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'
import { QuickAddDialog } from './components/QuickAddDialog'
import { FeatureTimeline } from './components/FeatureTimeline'

function AppContent() {
  const commandPalette = useCommandPalette();
  // Initialize keyboard shortcuts
  useKeyboardShortcuts();

  return (
    <>
      <CommandPalette isOpen={commandPalette.isOpen} onClose={commandPalette.close} />
      <ShortcutsHelpOverlay />
      <ShortcutsHelpButton />
      <QuickAddDialog />
      <Toaster
        position="top-right"
        toastOptions={{
          // Default options
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          // Success
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          // Error
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="specs" element={<SpecExplorer />} />
          <Route path="kanban" element={<KanbanBoard />} />
          <Route path="timeline" element={<FeatureTimeline />} />
          <Route path="task/:featureId" element={<TaskViewer />} />
          <Route path="activity" element={<ActivityLog />} />
          <Route path="config" element={<ConfigEditor />} />
        </Route>
      </Routes>
    </>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
