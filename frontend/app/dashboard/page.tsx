'use client'

import { useSession } from 'next-auth/react'
import { FileText, Users, CheckCircle, AlertCircle } from 'lucide-react'
import Link from 'next/link'

export default function DashboardPage() {
  const { data: session } = useSession()

  const stats = [
    {
      name: 'Total Articles',
      value: '12',
      icon: FileText,
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      name: 'Active Users',
      value: '24',
      icon: Users,
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
    {
      name: 'Citations Validated',
      value: '1,234',
      icon: CheckCircle,
      color: 'text-purple-600',
      bg: 'bg-purple-100',
    },
    {
      name: 'Requires Review',
      value: '45',
      icon: AlertCircle,
      color: 'text-orange-600',
      bg: 'bg-orange-100',
    },
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {session?.user?.name?.split(' ')[0] || 'User'}!
        </h1>
        <p className="text-gray-600 mt-2">
          Here's what's happening with your citation system today.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-lg shadow-sm border p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.name}</p>
                <p className="text-3xl font-bold mt-2">{stat.value}</p>
              </div>
              <div className={`${stat.bg} p-3 rounded-lg`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/dashboard/articles"
            className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FileText className="h-8 w-8 text-blue-600 mb-2" />
            <h3 className="font-semibold">Manage Articles</h3>
            <p className="text-sm text-gray-600 mt-1">
              View and manage all articles
            </p>
          </Link>

          <Link
            href="/dashboard/users"
            className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Users className="h-8 w-8 text-green-600 mb-2" />
            <h3 className="font-semibold">Manage Users</h3>
            <p className="text-sm text-gray-600 mt-1">
              Add and manage team members
            </p>
          </Link>

          <button className="p-4 border rounded-lg hover:bg-gray-50 transition-colors text-left">
            <CheckCircle className="h-8 w-8 text-purple-600 mb-2" />
            <h3 className="font-semibold">Review Citations</h3>
            <p className="text-sm text-gray-600 mt-1">
              Review flagged citations
            </p>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <div className="space-y-4">
          <div className="flex items-start gap-3 pb-4 border-b">
            <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="h-4 w-4 text-green-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm">
                <span className="font-medium">Article #123</span> completed R2 validation
              </p>
              <p className="text-xs text-gray-500 mt-1">2 hours ago</p>
            </div>
          </div>

          <div className="flex items-start gap-3 pb-4 border-b">
            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
              <Users className="h-4 w-4 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm">
                <span className="font-medium">New user</span> added to the system
              </p>
              <p className="text-xs text-gray-500 mt-1">5 hours ago</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="h-8 w-8 rounded-full bg-orange-100 flex items-center justify-center">
              <AlertCircle className="h-4 w-4 text-orange-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm">
                <span className="font-medium">12 citations</span> flagged for manual review
              </p>
              <p className="text-xs text-gray-500 mt-1">1 day ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
