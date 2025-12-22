import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import {
    HomeIcon,
    DocumentTextIcon,
    ClockIcon,
    Cog6ToothIcon,
    Bars3Icon,
    XMarkIcon,
    SunIcon,
    MoonIcon,
    ViewColumnsIcon,
    ChevronDoubleLeftIcon,
    ChevronDoubleRightIcon,
} from '@heroicons/react/24/outline'
import { useWebSocket } from '../hooks/useWebSocket'
import { getApiBaseUrl, getWebSocketUrl } from '../utils/api'
import { SessionBanner } from './SessionBanner'
import { SkipLink } from '../utils/accessibility'
import { SessionTimerWidget, useSessionTimer } from './SessionTimer'

interface ActiveSession {
    id: number;
    date: string;
    focus: string;
    started_at?: string;
}

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Spec Explorer', href: '/specs', icon: DocumentTextIcon },
    { name: 'Kanban Board', href: '/kanban', icon: ViewColumnsIcon },
    { name: 'Activity Log', href: '/activity', icon: ClockIcon },
    { name: 'Config', href: '/config', icon: Cog6ToothIcon },
]

function useTheme() {
    const [darkMode, setDarkMode] = useState(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem('klondike-dark-mode')
            if (stored !== null) {
                return stored === 'true'
            }
            return window.matchMedia('(prefers-color-scheme: dark)').matches
        }
        return false
    })

    useEffect(() => {
        const root = document.documentElement
        if (darkMode) {
            root.classList.add('dark')
        } else {
            root.classList.remove('dark')
        }
        localStorage.setItem('klondike-dark-mode', String(darkMode))
    }, [darkMode])

    return [darkMode, setDarkMode] as const
}

export function Layout() {
    const location = useLocation()
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem('klondike-sidebar-collapsed')
            return stored === 'true'
        }
        return false
    })
    const [darkMode, setDarkMode] = useTheme()
    const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)

    // Persist sidebar collapsed state
    useEffect(() => {
        localStorage.setItem('klondike-sidebar-collapsed', String(sidebarCollapsed))
    }, [sidebarCollapsed])

    // Initialize session timer from active session data
    useSessionTimer(activeSession ? {
        session_number: activeSession.id,
        focus: activeSession.focus,
        started_at: activeSession.started_at,
    } : null)

    // WebSocket for live updates
    const { lastMessage } = useWebSocket(getWebSocketUrl('/api/updates'))

    // Fetch session status
    const fetchSessionStatus = async () => {
        try {
            const response = await fetch(`${getApiBaseUrl()}/api/status`)
            if (response.ok) {
                const data = await response.json()
                if (data.is_session_active && data.current_session) {
                    setActiveSession(data.current_session)
                } else if (data.is_session_active && data.last_session) {
                    setActiveSession(data.last_session)
                } else {
                    setActiveSession(null)
                }
            }
        } catch {
            // Silently fail - banner is not critical
        }
    }

    // Fetch on mount
    useEffect(() => {
        fetchSessionStatus()
    }, [])

    // Refetch on WebSocket updates
    useEffect(() => {
        if (lastMessage) {
            fetchSessionStatus()
        }
    }, [lastMessage])

    // Close sidebar on route change (mobile)
    useEffect(() => {
        setSidebarOpen(false)
    }, [location.pathname])

    return (
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
            {/* Skip link for keyboard navigation */}
            <SkipLink targetId="main-content" />

            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <div
                className={`
                    fixed inset-y-0 left-0 z-50 bg-white dark:bg-gray-800 shadow-lg
                    transform transition-all duration-200 ease-in-out
                    ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                    md:translate-x-0
                    ${sidebarCollapsed ? 'md:w-16' : 'md:w-64'}
                    w-64
                `}
            >
                {/* Header with project name and close/collapse buttons */}
                <div className="flex h-16 items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4">
                    {!sidebarCollapsed && (
                        <h1 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">🎯 Klondike</h1>
                    )}
                    {sidebarCollapsed && (
                        <span className="text-xl mx-auto">🎯</span>
                    )}
                    <button
                        onClick={() => setSidebarOpen(false)}
                        aria-label="Close sidebar"
                        className="md:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                        <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                    </button>
                    <button
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                        className="hidden md:block p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                        {sidebarCollapsed ? (
                            <ChevronDoubleRightIcon className="h-5 w-5" aria-hidden="true" />
                        ) : (
                            <ChevronDoubleLeftIcon className="h-5 w-5" aria-hidden="true" />
                        )}
                    </button>
                </div>

                {/* Navigation */}
                <nav className="mt-6 px-3 flex-1" aria-label="Main navigation">
                    {navigation.map((item) => {
                        const isActive = location.pathname === item.href ||
                            (item.href === '/specs' && location.pathname.startsWith('/task/'))
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                aria-current={isActive ? 'page' : undefined}
                                title={sidebarCollapsed ? item.name : undefined}
                                className={`
                                    flex items-center gap-3 rounded-lg mb-2 transition-colors
                                    ${sidebarCollapsed ? 'justify-center px-3 py-3' : 'px-4 py-3'}
                                    ${isActive
                                        ? 'bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                    }
                                `}
                            >
                                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                                {!sidebarCollapsed && (
                                    <span className="font-medium">{item.name}</span>
                                )}
                            </Link>
                        )
                    })}
                </nav>

                {/* Session timer widget - only show when not collapsed */}
                {!sidebarCollapsed && (
                    <div className="px-3 mt-4">
                        <SessionTimerWidget variant="compact" />
                    </div>
                )}

                {/* Dark mode toggle */}
                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                        onClick={() => setDarkMode(!darkMode)}
                        aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                        title={sidebarCollapsed ? (darkMode ? 'Light Mode' : 'Dark Mode') : undefined}
                        className={`
                            flex items-center gap-3 w-full rounded-lg text-gray-700 dark:text-gray-300 
                            hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors
                            ${sidebarCollapsed ? 'justify-center px-3 py-3' : 'px-4 py-3'}
                        `}
                    >
                        {darkMode ? (
                            <>
                                <SunIcon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                                {!sidebarCollapsed && <span className="font-medium">Light Mode</span>}
                            </>
                        ) : (
                            <>
                                <MoonIcon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                                {!sidebarCollapsed && <span className="font-medium">Dark Mode</span>}
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Mobile header with hamburger */}
            <div className="fixed top-0 left-0 right-0 z-30 h-16 bg-white dark:bg-gray-800 shadow-sm md:hidden flex items-center px-4">
                <button
                    onClick={() => setSidebarOpen(true)}
                    aria-label="Open navigation menu"
                    className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                    <Bars3Icon className="h-6 w-6" aria-hidden="true" />
                </button>
                <h1 className="ml-3 text-lg font-bold text-indigo-600 dark:text-indigo-400">🎯 Klondike</h1>
            </div>

            {/* Main content */}
            <div className={`pt-16 md:pt-0 transition-all duration-200 ${sidebarCollapsed ? 'md:pl-16' : 'md:pl-64'}`}>
                {/* Active session banner */}
                {activeSession && (
                    <SessionBanner
                        sessionNumber={activeSession.id}
                        focus={activeSession.focus}
                        date={activeSession.date}
                    />
                )}
                <main id="main-content" className="p-4 md:p-8" role="main" tabIndex={-1}>
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
