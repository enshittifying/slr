'use client'

import { useSession, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { BookOpen, FileText, Users, LogOut, Menu, X } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login')
    }
  }, [status, router])

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!session) {
    return null
  }

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: BookOpen },
    { name: 'Articles', href: '/dashboard/articles', icon: FileText },
    { name: 'Users', href: '/dashboard/users', icon: Users },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar toggle */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="h-6 w-6 text-blue-600" />
          <span className="font-bold">SLR</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg hover:bg-gray-100"
        >
          {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r transform transition-transform lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="p-6 border-b">
            <div className="flex items-center gap-2">
              <BookOpen className="h-8 w-8 text-blue-600" />
              <div>
                <div className="font-bold text-lg">Stanford Law Review</div>
                <div className="text-xs text-gray-500">Citation System</div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center gap-3 px-4 py-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.name}</span>
              </Link>
            ))}
          </nav>

          {/* User info */}
          <div className="p-4 border-t">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
                {session.user?.name?.charAt(0) || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm truncate">
                  {session.user?.name || 'User'}
                </div>
                <div className="text-xs text-gray-500 truncate">
                  {session.user?.email}
                </div>
              </div>
            </div>
            <button
              onClick={() => signOut({ callbackUrl: '/login' })}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        <main className="pt-16 lg:pt-0">
          {children}
        </main>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
