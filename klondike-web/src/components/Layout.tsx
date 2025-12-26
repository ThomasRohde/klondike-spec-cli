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
    CalendarDaysIcon,
    ShareIcon,
    SwatchIcon,
} from '@heroicons/react/24/outline'
import { useWebSocket } from '../hooks/useWebSocket'
import { getApiBaseUrl, getWebSocketUrl } from '../utils/api'
import { SessionBanner } from './SessionBanner'
import { SkipLink } from '../utils/accessibility'
import { ThemeCustomizer, useTheme } from './ThemeCustomizer'

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
    { name: 'Timeline', href: '/timeline', icon: CalendarDaysIcon },
    { name: 'Dependencies', href: '/dependencies', icon: ShareIcon },
    { name: 'Activity Log', href: '/activity', icon: ClockIcon },
    { name: 'Config', href: '/config', icon: Cog6ToothIcon },
]

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
    const { isDark, setMode, settings } = useTheme()
    const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)
    const [showThemeCustomizer, setShowThemeCustomizer] = useState(false)

    const toggleTheme = () => {
        if (settings.mode === 'system') {
            setMode(isDark ? 'light' : 'dark');
        } else if (settings.mode === 'dark') {
            setMode('light');
        } else {
            setMode('dark');
        }
    }

    // Persist sidebar collapsed state
    useEffect(() => {
        localStorage.setItem('klondike-sidebar-collapsed', String(sidebarCollapsed))
    }, [sidebarCollapsed])

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
        // eslint-disable-next-line react-hooks/set-state-in-effect
        void fetchSessionStatus()
    }, [])

    // Refetch on WebSocket updates
    useEffect(() => {
        if (lastMessage) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            void fetchSessionStatus()
        }
    }, [lastMessage])

    // Close sidebar on route change (mobile)
    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSidebarOpen(false)
    }, [location.pathname])

    return (
        <div className="min-h-screen bg-[var(--parchment-100)] dark:bg-[var(--slate-900)]">
            {/* Skip link for keyboard navigation */}
            <SkipLink targetId="main-content" />

            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
                    sidebar fixed inset-y-0 left-0 z-50 shadow-xl
                    transform transition-all duration-300 ease-out
                    ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                    md:translate-x-0
                    ${sidebarCollapsed ? 'md:w-20' : 'md:w-72'}
                    w-72
                `}
            >
                {/* Decorative top border */}
                <div className="absolute top-0 left-0 right-0 h-1 gold-gradient-bg" />

                {/* Header with project name and close/collapse buttons */}
                <div className="sidebar-header h-16">
                    {!sidebarCollapsed && (
                        <div className="flex items-center gap-2">
                            <span className="spade-logo">♠</span>
                            <h1 className="text-xl font-display font-bold gold-gradient-text">
                                Klondike
                            </h1>
                        </div>
                    )}
                    {sidebarCollapsed && (
                        <span className="spade-logo mx-auto">♠</span>
                    )}
                    <button
                        onClick={() => setSidebarOpen(false)}
                        aria-label="Close sidebar"
                        className="md:hidden p-2 rounded-lg text-[var(--neutral-slate)] hover:bg-[var(--parchment-200)] dark:hover:bg-white/10 transition-colors"
                    >
                        <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                    </button>
                    <button
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                        className="hidden md:flex items-center justify-center w-8 h-8 rounded-lg text-[var(--neutral-slate)] hover:bg-[var(--parchment-200)] dark:hover:bg-white/10 transition-colors"
                    >
                        {sidebarCollapsed ? (
                            <ChevronDoubleRightIcon className="h-4 w-4" aria-hidden="true" />
                        ) : (
                            <ChevronDoubleLeftIcon className="h-4 w-4" aria-hidden="true" />
                        )}
                    </button>
                </div>

                {/* Navigation */}
                <nav className="mt-6 px-3 flex-1" aria-label="Main navigation">
                    {navigation.map((item, index) => {
                        const isActive = location.pathname === item.href ||
                            (item.href === '/specs' && location.pathname.startsWith('/task/'))
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                aria-current={isActive ? 'page' : undefined}
                                title={sidebarCollapsed ? item.name : undefined}
                                className={`
                                    nav-link mb-1
                                    ${sidebarCollapsed ? 'justify-center px-3' : 'px-4'}
                                    ${isActive ? 'active' : ''}
                                `}
                                style={{ animationDelay: `${index * 50}ms` }}
                            >
                                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                                {!sidebarCollapsed && (
                                    <span className="font-medium">{item.name}</span>
                                )}
                            </Link>
                        )
                    })}
                </nav>

                {/* Bottom section with decorative line */}
                <div className="absolute bottom-0 left-0 right-0">
                    <div className="deco-line mx-4 mb-4" />
                    <div className="p-4 space-y-1">
                        <button
                            onClick={() => setShowThemeCustomizer(true)}
                            aria-label="Customize theme"
                            title={sidebarCollapsed ? 'Theme Settings' : undefined}
                            className={`
                                nav-link w-full
                                ${sidebarCollapsed ? 'justify-center px-3' : 'px-4'}
                            `}
                        >
                            <SwatchIcon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                            {!sidebarCollapsed && <span className="font-medium">Theme</span>}
                        </button>
                        <button
                            onClick={toggleTheme}
                            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                            title={sidebarCollapsed ? (isDark ? 'Light Mode' : 'Dark Mode') : undefined}
                            className={`
                                nav-link w-full
                                ${sidebarCollapsed ? 'justify-center px-3' : 'px-4'}
                            `}
                        >
                            {isDark ? (
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
            </aside>

            {/* Mobile header with hamburger */}
            <header className="fixed top-0 left-0 right-0 z-30 h-16 bg-white dark:bg-[var(--slate-850)] shadow-sm md:hidden">
                <div className="flex items-center justify-between h-full px-4">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setSidebarOpen(true)}
                            aria-label="Open navigation menu"
                            className="p-2 rounded-lg text-[var(--neutral-slate)] hover:bg-[var(--parchment-200)] dark:hover:bg-white/10 transition-colors"
                        >
                            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
                        </button>
                        <div className="flex items-center gap-2">
                            <span className="spade-logo text-xl">♠</span>
                            <h1 className="text-lg font-display font-bold gold-gradient-text">
                                Klondike
                            </h1>
                        </div>
                    </div>
                    <button
                        onClick={toggleTheme}
                        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                        className="p-2 rounded-lg text-[var(--neutral-slate)] hover:bg-[var(--parchment-200)] dark:hover:bg-white/10 transition-colors"
                    >
                        {isDark ? (
                            <SunIcon className="h-5 w-5" aria-hidden="true" />
                        ) : (
                            <MoonIcon className="h-5 w-5" aria-hidden="true" />
                        )}
                    </button>
                </div>
                {/* Bottom border gradient */}
                <div className="absolute bottom-0 left-0 right-0 h-px gold-gradient-bg opacity-50" />
            </header>

            {/* Main content */}
            <div className={`pt-16 md:pt-0 transition-all duration-300 ${sidebarCollapsed ? 'md:pl-20' : 'md:pl-72'}`}>
                {/* Active session banner */}
                {activeSession && (
                    <SessionBanner
                        sessionNumber={activeSession.id}
                        focus={activeSession.focus}
                        date={activeSession.date}
                    />
                )}
                <main
                    id="main-content"
                    className="p-4 md:p-8 min-h-screen"
                    role="main"
                    tabIndex={-1}
                >
                    <Outlet />
                </main>
            </div>

            {/* Theme Customizer Modal */}
            {showThemeCustomizer && (
                <ThemeCustomizer onClose={() => setShowThemeCustomizer(false)} />
            )}
        </div>
    )
}
