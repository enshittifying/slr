import Link from 'next/link'
import { BookOpen, CheckCircle, FileText, Users } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">Stanford Law Review</span>
          </div>
          <Link
            href="/login"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </header>

      {/* Hero */}
      <main className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Automated Citation Checking System
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            Streamline your citation validation process with AI-powered automation.
            Verify Bluebook compliance, check proposition support, and manage your
            editorial workflow—all in one place.
          </p>

          <div className="flex gap-4 justify-center mb-16">
            <Link
              href="/login"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold"
            >
              Get Started
            </Link>
            <Link
              href="#features"
              className="px-8 py-3 border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-lg font-semibold"
            >
              Learn More
            </Link>
          </div>

          {/* Features */}
          <div id="features" className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="p-6 bg-white rounded-lg shadow-sm border">
              <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Automated Validation</h3>
              <p className="text-gray-600">
                Three-stage pipeline validates citations against Bluebook rules and
                verifies proposition support using GPT-4.
              </p>
            </div>

            <div className="p-6 bg-white rounded-lg shadow-sm border">
              <FileText className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Article Management</h3>
              <p className="text-gray-600">
                Track articles through the editorial process with real-time status
                updates and citation statistics.
              </p>
            </div>

            <div className="p-6 bg-white rounded-lg shadow-sm border">
              <Users className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Team Collaboration</h3>
              <p className="text-gray-600">
                Assign tasks, track progress, and manage your editorial team with
                role-based permissions.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-16 py-8">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p>© 2025 Stanford Law Review. All rights reserved.</p>
          <p className="mt-2 text-sm">
            Powered by AI • Built for Academic Excellence
          </p>
        </div>
      </footer>
    </div>
  )
}
