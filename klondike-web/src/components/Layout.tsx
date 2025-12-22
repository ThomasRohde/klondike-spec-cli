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
} from '@heroicons/react/24/outline'

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Spec Explorer', href: '/specs', icon: DocumentTextIcon },
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
    const [darkMode, setDarkMode] = useTheme()

    // Close sidebar on route change (mobile)
    useEffect(() => {
        setSidebarOpen(false)
    }, [location.pathname])

    return (
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
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
                    fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg
                    transform transition-transform duration-200 ease-in-out
                    ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                    md:translate-x-0
                `}
            >
                {/* Header with project name and close button (mobile) */}
                <div className="flex h-16 items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4">
                    <h1 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">🎯 Klondike</h1>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="md:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                        <XMarkIcon className="h-5 w-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="mt-6 px-3 flex-1">
                    {navigation.map((item) => {
                        const isActive = location.pathname === item.href ||
                            (item.href === '/specs' && location.pathname.startsWith('/task/'))
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                className={`
                                    flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-colors
                                    ${isActive
                                        ? 'bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                    }
                                `}
                            >
                                <item.icon className="h-5 w-5" />
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        )
                    })}
                </nav>

                {/* Dark mode toggle */}
                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                        onClick={() => setDarkMode(!darkMode)}
                        className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                        {darkMode ? (
                            <>
                                <SunIcon className="h-5 w-5" />
                                <span className="font-medium">Light Mode</span>
                            </>
                        ) : (
                            <>
                                <MoonIcon className="h-5 w-5" />
                                <span className="font-medium">Dark Mode</span>
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Mobile header with hamburger */}
            <div className="fixed top-0 left-0 right-0 z-30 h-16 bg-white dark:bg-gray-800 shadow-sm md:hidden flex items-center px-4">
                <button
                    onClick={() => setSidebarOpen(true)}
                    className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                    <Bars3Icon className="h-6 w-6" />
                </button>
                <h1 className="ml-3 text-lg font-bold text-indigo-600 dark:text-indigo-400">🎯 Klondike</h1>
            </div>

            {/* Main content */}
            <div className="md:pl-64 pt-16 md:pt-0">
                <main className="p-4 md:p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
