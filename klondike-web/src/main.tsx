import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { registerServiceWorker } from './components/OfflineSupport'
import { initializeTheme } from './components/ThemeCustomizer'

// Initialize theme before rendering
initializeTheme()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

// Register service worker for offline support
registerServiceWorker()
