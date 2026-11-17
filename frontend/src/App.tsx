import { useState, useEffect } from 'react'

interface HealthResponse {
  status: string
  app: string
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
        return res.json()
      })
      .then((data: HealthResponse) => {
        setHealth(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 text-indigo-400 mb-6 border border-indigo-500/30">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Cuort Support Orchestrator</h1>
        <p className="text-slate-400 text-sm mb-6">
          AI-Powered Multi-Agent Complaint Management Platform
        </p>

        <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50 mb-6 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-300">Backend API Status:</span>
          {loading && <span className="text-xs bg-amber-500/20 text-amber-400 px-3 py-1 rounded-full border border-amber-500/30">Connecting...</span>}
          {!loading && health && (
            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/30 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Connected ({health.app} - {health.status})
            </span>
          )}
          {!loading && error && (
            <span className="text-xs bg-rose-500/20 text-rose-400 px-3 py-1 rounded-full border border-rose-500/30">
              Offline (Start Backend)
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 text-left">
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="p-3 rounded-lg bg-slate-800 hover:bg-slate-700 transition border border-slate-700 text-xs font-medium text-indigo-300 block text-center"
          >
            Open Swagger Docs ↗
          </a>
          <a
            href="http://127.0.0.1:8000/api/v1/health"
            target="_blank"
            rel="noreferrer"
            className="p-3 rounded-lg bg-slate-800 hover:bg-slate-700 transition border border-slate-700 text-xs font-medium text-slate-300 block text-center"
          >
            Raw Health Endpoint ↗
          </a>
        </div>
      </div>
    </div>
  )
}

export default App
