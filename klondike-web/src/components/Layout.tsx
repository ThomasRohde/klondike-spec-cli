import { Outlet, Link, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  DocumentTextIcon,
  ClockIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Spec Explorer', href: '/specs', icon: DocumentTextIcon },
  { name: 'Activity Log', href: '/activity', icon: ClockIcon },
  { name: 'Config', href: '/config', icon: Cog6ToothIcon },
]

export function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg">
        <div className="flex h-16 items-center justify-center border-b border-gray-200">
          <h1 className="text-xl font-bold text-indigo-600">🎯 Klondike</h1>
        </div>
        <nav className="mt-6 px-3">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-colors
                  ${isActive
                    ? 'bg-indigo-50 text-indigo-600'
                    : 'text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
