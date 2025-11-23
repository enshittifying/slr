'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import { api, setAuthToken } from '@/lib/api-client'
import { FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react'

export default function ArticlesPage() {
  const { data: session } = useSession()

  useEffect(() => {
    if (session?.accessToken) {
      setAuthToken(session.accessToken)
    }
  }, [session])

  const { data: articlesData, isLoading } = useQuery({
    queryKey: ['articles'],
    queryFn: async () => {
      const response = await api.articles.list({ per_page: 50 })
      return response.data
    },
    enabled: !!session?.accessToken,
  })

  const getStatusBadge = (status: string) => {
    const config = {
      draft: { color: 'bg-gray-100 text-gray-800', icon: Clock },
      sp_in_progress: { color: 'bg-blue-100 text-blue-800', icon: Clock },
      r1_in_progress: { color: 'bg-purple-100 text-purple-800', icon: Clock },
      r2_in_progress: { color: 'bg-orange-100 text-orange-800', icon: AlertCircle },
      completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      published: { color: 'bg-emerald-100 text-emerald-800', icon: CheckCircle },
    }
    return config[status as keyof typeof config] || config.draft
  }

  if (isLoading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading articles...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Articles</h1>
          <p className="text-gray-600 mt-2">
            Manage articles and track citation validation
          </p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          New Article
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <FileText className="h-8 w-8 text-blue-600 mb-2" />
          <p className="text-sm text-gray-600">Total Articles</p>
          <p className="text-2xl font-bold mt-1">{articlesData?.total || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <Clock className="h-8 w-8 text-orange-600 mb-2" />
          <p className="text-sm text-gray-600">In Progress</p>
          <p className="text-2xl font-bold mt-1">
            {articlesData?.items?.filter((a: any) =>
              a.status.includes('in_progress')
            ).length || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <CheckCircle className="h-8 w-8 text-green-600 mb-2" />
          <p className="text-sm text-gray-600">Completed</p>
          <p className="text-2xl font-bold mt-1">
            {articlesData?.items?.filter((a: any) =>
              a.status === 'completed'
            ).length || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <AlertCircle className="h-8 w-8 text-purple-600 mb-2" />
          <p className="text-sm text-gray-600">Published</p>
          <p className="text-2xl font-bold mt-1">
            {articlesData?.items?.filter((a: any) =>
              a.status === 'published'
            ).length || 0}
          </p>
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {articlesData?.items?.map((article: any) => {
          const statusConfig = getStatusBadge(article.status)
          const StatusIcon = statusConfig.icon

          return (
            <div
              key={article.id}
              className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-gray-900 line-clamp-2">
                    {article.title}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    By {article.author_name || 'Unknown'}
                  </p>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Volume {article.volume_number}</span>
                  <span className="text-gray-600">Issue {article.issue_number}</span>
                </div>

                <div className="flex items-center gap-2">
                  <StatusIcon className="h-4 w-4" />
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${statusConfig.color}`}>
                    {article.status.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-xs text-gray-500">
                  Created {new Date(article.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {articlesData?.items?.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No articles yet
          </h3>
          <p className="text-gray-600 mb-6">
            Get started by creating your first article
          </p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Create Article
          </button>
        </div>
      )}
    </div>
  )
}
